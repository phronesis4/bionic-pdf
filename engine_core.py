import math
import os
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*fitz.*")

import pymupdf

from neuro_enhancer import (
    FONT_SCALE_COMPENSATION,
    IRLEN_TINTS,
    STOP_WORDS,
    bionic_word_split,
    measure_text_width,
    resolve_font_resources,
    sanitize_text,
)


def parse_page_range(range_str: str, total_pages: int) -> list[int]:
    if not range_str.strip() or range_str.strip().lower() in ["all", "a", ""]:
        return list(range(total_pages))

    pages = set()
    parts = range_str.replace(" ", "").split(",")
    for part in parts:
        if "-" in part:
            sub = part.split("-")
            if len(sub) == 2 and sub[0].isdigit() and sub[1].isdigit():
                start = max(1, int(sub[0]))
                end = min(total_pages, int(sub[1]))
                for p in range(start, end + 1):
                    pages.add(p - 1)
        elif part.isdigit():
            p = int(part)
            if 1 <= p <= total_pages:
                pages.add(p - 1)

    return sorted(list(pages)) if pages else list(range(total_pages))


def normalize_angle_and_vector(dir_vector: tuple[float, float]) -> tuple[int, float, float]:
    """
    Maps text direction vectors to cardinal angles (0, 90, 180, 270 degrees)
    and returns (angle_degrees, unit_dx, unit_dy).
    Returns (-1, 0.0, 0.0) for diagonal watermarks.
    """
    dx, dy = dir_vector[0], dir_vector[1]
    raw_angle = round(math.degrees(math.atan2(dy, dx))) % 360

    if raw_angle <= 8 or raw_angle >= 352:
        return 0, 1.0, 0.0
    elif 82 <= raw_angle <= 98:
        return 90, 0.0, 1.0
    elif 172 <= raw_angle <= 188:
        return 180, -1.0, 0.0
    elif 262 <= raw_angle <= 278:
        return 270, 0.0, -1.0

    return -1, 0.0, 0.0


def process_single_page_isolated(args: tuple) -> tuple[int, int]:
    pdf_path, p_idx, fixation, font_mode, neuro_config, password, out_temp_page_path = args

    src_doc = pymupdf.open(pdf_path)
    if src_doc.is_encrypted and password:
        src_doc.authenticate(password)

    page_doc = pymupdf.open()
    page_doc.insert_pdf(src_doc, from_page=p_idx, to_page=p_idx)
    src_doc.close()

    page = page_doc[0]
    page_width = page.rect.width
    page_height = page.rect.height

    # Detect table boundaries to protect cell structures
    try:
        tabs = page.find_tables()
        table_rects = [pymupdf.Rect(t.bbox) for t in tabs]
    except Exception:
        table_rects = []

    def is_in_table(rect_or_point) -> bool:
        for tr in table_rects:
            if tr.intersects(rect_or_point):
                return True
        return False

    text_page = page.get_text("dict", flags=pymupdf.TEXTFLAGS_TEXT)
    blocks = text_page.get("blocks", [])

    redactions = []
    insertions = []
    paragraph_bars = []
    page_word_count = 0

    do_dim_stops = neuro_config.get("stop_word_dimming", False)
    do_left_anchor = neuro_config.get("left_anchor_track", False)
    do_letter_spacing = neuro_config.get("micro_letter_spacing", False)
    do_word_gap = neuro_config.get("word_gap_expansion", False)
    do_dual_tone = neuro_config.get("dual_tone_words", False)
    do_narrow_column = neuro_config.get("narrow_column", False)
    canvas_tint_key = neuro_config.get("canvas_tint", "none")

    font_base_scale = FONT_SCALE_COMPENSATION.get(font_mode, 1.0)
    tracking_delta = (0.28 if do_letter_spacing else 0.0) * font_base_scale
    word_gap_mult = 1.18 if do_word_gap else 1.0

    for block in blocks:
        if block.get("type") != 0:
            continue

        b_bbox = block.get("bbox", (0, 0, 0, 0))
        lines = block.get("lines", [])
        block_in_table = is_in_table(b_bbox)

        # Draw left anchor guide rail only on narrative paragraphs outside tables
        if do_left_anchor and not block_in_table and (b_bbox[3] - b_bbox[1] > 25) and (b_bbox[0] < 80):
            paragraph_bars.append((
                max(16, b_bbox[0] - 8),
                b_bbox[1] + 2,
                max(18, b_bbox[0] - 5),
                b_bbox[3] - 2,
            ))

        for line in lines:
            dir_vector = line.get("dir", (1.0, 0.0))
            angle, udx, udy = normalize_angle_and_vector(dir_vector)

            # Skip diagonal watermarks
            if angle == -1:
                continue

            for span in line.get("spans", []):
                raw_text = span.get("text", "")
                text = sanitize_text(raw_text)

                if not text.strip():
                    continue

                bbox = span.get("bbox")
                raw_size = span.get("size", 10.0)
                size = raw_size * font_base_scale
                origin = span.get("origin")
                color = span.get("color", 0)
                font_name = span.get("font", "")
                flags = span.get("flags", 0)

                is_italic = bool(flags & 2) or ("italic" in font_name.lower()) or ("-it" in font_name.lower())
                b_font, n_font, b_file, n_file = resolve_font_resources(font_mode, is_italic)

                if angle in (0, 180):
                    orig_span_len = bbox[2] - bbox[0]
                    margin_limit = max(20.0, page_width - origin[0] - 25.0) if angle == 0 else max(20.0, origin[0] - 25.0)
                else:  # Vertical / rotated 90 / 270 degree table headers
                    orig_span_len = bbox[3] - bbox[1]
                    margin_limit = max(20.0, page_height - origin[1] - 25.0) if angle == 90 else max(20.0, origin[1] - 25.0)

                max_allowed_len = min(orig_span_len, margin_limit) if orig_span_len > 0 else margin_limit

                if do_narrow_column and not block_in_table and max_allowed_len > 400:
                    max_allowed_len = 400

                raw_words = text.split(" ")
                tokens = []
                total_bionic_w = 0.0
                base_space_w = measure_text_width(" ", n_font, n_file, size) * word_gap_mult

                for idx, w in enumerate(raw_words):
                    if idx > 0:
                        total_bionic_w += base_space_w + tracking_delta

                    if not w:
                        tokens.append(("", "", False, idx))
                        continue

                    page_word_count += 1
                    clean_w_lower = w.strip(".,!?;:\"')]}*·•[]()<>{}-").lower()
                    is_stop_word = clean_w_lower in STOP_WORDS

                    bold_p, norm_p = bionic_word_split(w, fixation=fixation)
                    tokens.append((bold_p, norm_p, is_stop_word, idx))

                    if bold_p:
                        total_bionic_w += measure_text_width(bold_p, b_font, b_file, size) + tracking_delta
                    if norm_p:
                        total_bionic_w += measure_text_width(norm_p, n_font, n_file, size) + tracking_delta

                scale = 1.0
                if total_bionic_w > max_allowed_len and max_allowed_len > 0:
                    scale = max_allowed_len / total_bionic_w
                    scale = max(0.55, min(1.0, scale))

                if isinstance(color, int):
                    r = ((color >> 16) & 0xFF) / 255.0
                    g = ((color >> 8) & 0xFF) / 255.0
                    b = (color & 0xFF) / 255.0
                    text_color = (r, g, b)
                else:
                    text_color = (0, 0, 0)

                redactions.append(pymupdf.Rect(bbox))
                insertions.append({
                    "tokens": tokens,
                    "start_x": origin[0],
                    "start_y": origin[1],
                    "angle": angle,
                    "udx": udx,
                    "udy": udy,
                    "size": size * scale,
                    "space_w": (base_space_w + tracking_delta) * scale,
                    "tracking": tracking_delta * scale,
                    "b_font": b_font,
                    "n_font": n_font,
                    "b_file": b_file,
                    "n_file": n_file,
                    "color": text_color,
                })

    # Erase text without removing table borders or lines
    for r_rect in redactions:
        page.add_redact_annot(r_rect)

    try:
        page.apply_redactions(
            images=pymupdf.PDF_REDACT_IMAGE_NONE,
            graphics=pymupdf.PDF_REDACT_LINE_ART_NONE
        )
    except Exception:
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE)

    # Apply background tint behind all content
    tint_rgb = IRLEN_TINTS.get(canvas_tint_key)
    if tint_rgb is not None:
        page.draw_rect(page.rect, color=None, fill=tint_rgb, overlay=False)

    # Render left-margin guide rail
    if do_left_anchor:
        for x0, y0, x1, y1 in paragraph_bars:
            rect = pymupdf.Rect(x0, y0, x1, y1)
            page.draw_rect(rect, color=(0.14, 0.75, 0.55), fill=(0.14, 0.75, 0.55), width=0.5)

    # Insert text layer
    for item in insertions:
        curr_x = item["start_x"]
        curr_y = item["start_y"]
        angle = item["angle"]
        udx = item["udx"]
        udy = item["udy"]
        size = item["size"]
        space_w = item["space_w"]
        tracking = item["tracking"]
        b_font, n_font = item["b_font"], item["n_font"]
        b_file, n_file = item["b_file"], item["n_file"]
        base_color = item["color"]

        for (bold_part, norm_part, is_stop, word_idx) in item["tokens"]:
            if word_idx > 0:
                curr_x += udx * space_w
                curr_y += udy * space_w

            if not bold_part and not norm_part:
                continue

            if do_dim_stops and is_stop:
                word_color = (0.50, 0.54, 0.58)
            elif do_dual_tone:
                word_color = base_color if (word_idx % 2 == 0) else (0.10, 0.28, 0.55)
            else:
                word_color = base_color

            if bold_part:
                page.insert_text(
                    pymupdf.Point(curr_x, curr_y),
                    bold_part,
                    fontsize=size,
                    fontname=b_font,
                    fontfile=b_file if b_file else None,
                    color=word_color,
                    rotate=angle,
                )
                w_bold = measure_text_width(bold_part, b_font, b_file, size) + tracking
                curr_x += udx * w_bold
                curr_y += udy * w_bold

            if norm_part:
                page.insert_text(
                    pymupdf.Point(curr_x, curr_y),
                    norm_part,
                    fontsize=size,
                    fontname=n_font,
                    fontfile=n_file if n_file else None,
                    color=word_color,
                    rotate=angle,
                )
                w_norm = measure_text_width(norm_part, n_font, n_file, size) + tracking
                curr_x += udx * w_norm
                curr_y += udy * w_norm

    page_doc.save(out_temp_page_path)
    page_doc.close()

    return p_idx, page_word_count