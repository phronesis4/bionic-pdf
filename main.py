import os
import shutil
import sys
import tempfile
import time
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*fitz.*")

import pymupdf

from engine_core import parse_page_range, process_single_page_isolated
from neuro_enhancer import bionic_word_split, ensure_font_downloaded
from terminal_ui import (
    C_BOLD,
    C_CYAN,
    C_DIM,
    C_GREEN,
    C_MAGENTA,
    C_RED,
    C_RESET,
    C_YELLOW,
    display_stats,
    enable_windows_ansi,
    format_preview,
    print_banner,
    render_progress,
)

OUTPUT_DIR_NAME = "converted_bionic"


def get_unique_output_path(output_dir: str, base_name: str, ext: str) -> str:
    """Generates an incremental non-colliding filename to prevent overwriting."""
    target_path = os.path.join(output_dir, f"{base_name}_bionic{ext}")
    if not os.path.exists(target_path):
        return target_path

    counter = 1
    while True:
        candidate = os.path.join(output_dir, f"{base_name}_bionic_{counter}{ext}")
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def main():
    enable_windows_ansi()
    print_banner()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(current_dir, OUTPUT_DIR_NAME)
    os.makedirs(output_dir, exist_ok=True)

    pdf_files = [
        f for f in os.listdir(current_dir)
        if f.lower().endswith(".pdf") and not f.endswith("_bionic.pdf")
    ]

    if not pdf_files:
        print(f"{C_RED}[!] NO CANDIDATE PDFs DETECTED IN WORKSPACE:{C_RESET} {current_dir}")
        input(f"\n{C_DIM}Press ENTER to exit...{C_RESET}")
        return

    print(f"{C_CYAN}[>] DISCOVERED LOCAL TARGETS:{C_RESET}\n")
    for idx, filename in enumerate(pdf_files, 1):
        print(f"  {C_GREEN}[{idx:02d}]{C_RESET} {filename}")

    print(f"\n  {C_YELLOW}[00] BATCH PROCESS ALL DETECTED TARGETS{C_RESET}")
    print("-" * 65)

    while True:
        choice = input(f"\n{C_BOLD}SELECT TARGET ID > {C_RESET}").strip()
        if choice.isdigit():
            c = int(choice)
            if c == 0:
                selected_files = pdf_files
                break
            elif 1 <= c <= len(pdf_files):
                selected_files = [pdf_files[c - 1]]
                break
        print(f"{C_RED}[!] Invalid index selection.{C_RESET}")

    # Presets / Profile Selector
    print(f"\n{C_CYAN}[>] QUICK-PRESET OR CUSTOM CONFIGURATION:{C_RESET}\n")
    print(f"  {C_MAGENTA}[D] One-Click Dyslexia Mode{C_RESET}  (OpenDyslexic Font + Cream Tint + Anti-Crowding + Word Gap)")
    print(f"  {C_GREEN}[A] One-Click ADHD Mode{C_RESET}      (Atkinson Font + Stop-Word Dimming + Left Anchor Track)")
    print(f"  {C_CYAN}[P] My Preference{C_RESET}            (Atkinson + F3 + Letter-Spacing + Left Anchor + Narrow Column)")
    print(f"  {C_YELLOW}[C] Custom Multi-Select{C_RESET}      (Configure every typography and visual option)")

    preset_choice = input(f"\n{C_BOLD}SELECT PROFILE [Press Enter for P (My Preference)] > {C_RESET}").strip().upper()

    if preset_choice in ["P", ""]:
        selected_font_mode = "atkinson"
        selected_fixation = "F3"
        neuro_config = {
            "stop_word_dimming": False,
            "left_anchor_track": True,
            "micro_letter_spacing": True,
            "word_gap_expansion": False,
            "dual_tone_words": False,
            "narrow_column": True,
            "canvas_tint": "none",
        }
    elif preset_choice == "D":
        selected_font_mode = "opendyslexic"
        selected_fixation = "F3"
        neuro_config = {
            "stop_word_dimming": False,
            "left_anchor_track": True,
            "micro_letter_spacing": True,
            "word_gap_expansion": True,
            "dual_tone_words": False,
            "narrow_column": False,
            "canvas_tint": "cream",
        }
    elif preset_choice == "A":
        selected_font_mode = "atkinson"
        selected_fixation = "F3"
        neuro_config = {
            "stop_word_dimming": True,
            "left_anchor_track": True,
            "micro_letter_spacing": True,
            "word_gap_expansion": False,
            "dual_tone_words": False,
            "narrow_column": False,
            "canvas_tint": "none",
        }
    else:
        # Custom Step 1: Font Selector
        print(f"\n{C_CYAN}[>] SELECT ACCESSIBILITY TYPEFACE / FONT:{C_RESET}\n")
        print(f"  {C_GREEN}[1] OpenDyslexic Font{C_RESET}      (Bottom-weighted anti-letter-flipping geometry)")
        print(f"  {C_GREEN}[2] Atkinson Hyperlegible{C_RESET}  (Braille Inst. distinct character shapes)")
        print(f"  {C_GREEN}[3] Lexend Fluency Font{C_RESET}    (Engineered to reduce cognitive reading drag)")
        print(f"  {C_GREEN}[4] Modern Bionic Sans{C_RESET}     (Clean Helvetica/Inter style)")
        print(f"  {C_GREEN}[5] Classic Book Serif{C_RESET}     (Times Roman)")

        font_choice = input(f"\n{C_BOLD}SELECT FONT [Press Enter for 2 (Atkinson)] > {C_RESET}").strip()
        font_map = {"1": "opendyslexic", "2": "atkinson", "3": "lexend", "4": "bionic_sans", "5": "serif"}
        selected_font_mode = font_map.get(font_choice, "atkinson")

        # Custom Step 2: Fixation Selector
        sample_phrase = "Bionic Reading accelerates speed"
        print(f"\n{C_CYAN}[>] SELECT FIXATION PRESET (F1 - F5):{C_RESET}\n")
        print(f"  {C_GREEN}[1] F1 (~65% Bold){C_RESET}  Preview: {format_preview(sample_phrase, 'F1', bionic_word_split)}")
        print(f"  {C_GREEN}[2] F2 (~50% Bold){C_RESET}  Preview: {format_preview(sample_phrase, 'F2', bionic_word_split)}")
        print(f"  {C_GREEN}[3] F3 (~40% Bold){C_RESET}  Preview: {format_preview(sample_phrase, 'F3', bionic_word_split)}  {C_YELLOW}[Recommended]{C_RESET}")
        print(f"  {C_GREEN}[4] F4 (~30% Bold){C_RESET}  Preview: {format_preview(sample_phrase, 'F4', bionic_word_split)}")
        print(f"  {C_GREEN}[5] F5 (1-Letter){C_RESET}   Preview: {format_preview(sample_phrase, 'F5', bionic_word_split)}")

        fix_choice = input(f"\n{C_BOLD}SELECT FIXATION [Press Enter for 3 (F3)] > {C_RESET}").strip()
        fix_map = {"1": "F1", "2": "F2", "3": "F3", "4": "F4", "5": "F5"}
        selected_fixation = fix_map.get(fix_choice, "F3")

        # Custom Step 3: Enhancements Menu
        print(f"\n{C_CYAN}[>] ACCESSIBILITY ENHANCEMENTS (MULTI-SELECT):{C_RESET}")
        print(f"  {C_DIM}Enter comma-separated numbers (e.g. '3,6,7') or press Enter for recommended '3,6,7'{C_RESET}\n")
        print(f"  {C_GREEN}[1]{C_RESET} Stop-Word Dimming        (Dims 'the, is, and' to soft gray so keywords pop)")
        print(f"  {C_GREEN}[2]{C_RESET} Word-Gap Expansion       (Adds space between words so they don't blur)")
        print(f"  {C_GREEN}[3]{C_RESET} Micro Letter-Spacing     (Anti-crowding tracking between individual letters)")
        print(f"  {C_GREEN}[4]{C_RESET} Irlen Warm-Cream Tint    (Eliminates white screen/paper glare & visual vibration)")
        print(f"  {C_GREEN}[5]{C_RESET} Dual-Tone Alternating    (Alternates words charcoal/navy to stop line-jumping)")
        print(f"  {C_GREEN}[6]{C_RESET} Left-Margin Anchor Track (Adds a subtle teal guide rail on main paragraphs)")
        print(f"  {C_GREEN}[7]{C_RESET} Narrow Column Bound      (Constrains text width to 65-70 character saccades)")

        adhd_input = input(f"\n{C_BOLD}SELECT ENHANCEMENTS [Default: 3,6,7] > {C_RESET}").strip()
        if not adhd_input:
            adhd_input = "3,6,7"

        selections = [s.strip() for s in adhd_input.split(",")]
        neuro_config = {
            "stop_word_dimming": "1" in selections,
            "word_gap_expansion": "2" in selections,
            "micro_letter_spacing": "3" in selections,
            "canvas_tint": "cream" if "4" in selections else "none",
            "dual_tone_words": "5" in selections,
            "left_anchor_track": "6" in selections,
            "narrow_column": "7" in selections,
        }

    # Pre-download required custom fonts
    if selected_font_mode == "opendyslexic":
        ensure_font_downloaded("opendyslexic_reg")
        ensure_font_downloaded("opendyslexic_bold")
        ensure_font_downloaded("opendyslexic_it")
    elif selected_font_mode == "atkinson":
        ensure_font_downloaded("atkinson_reg")
        ensure_font_downloaded("atkinson_bold")
        ensure_font_downloaded("atkinson_it")
    elif selected_font_mode == "lexend":
        ensure_font_downloaded("lexend_reg")
        ensure_font_downloaded("lexend_bold")

    active_feature_names = []
    if selected_font_mode != "bionic_sans": active_feature_names.append(f"Font: {selected_font_mode.capitalize()}")
    if neuro_config.get("canvas_tint") != "none": active_feature_names.append(f"Irlen Tint: {neuro_config['canvas_tint'].capitalize()}")
    if neuro_config.get("word_gap_expansion"): active_feature_names.append("Word-Gap Expansion")
    if neuro_config.get("micro_letter_spacing"): active_feature_names.append("Micro Letter-Spacing")
    if neuro_config.get("dual_tone_words"): active_feature_names.append("Dual-Tone Alternating Words")
    if neuro_config.get("stop_word_dimming"): active_feature_names.append("Stop-Word Dimming")
    if neuro_config.get("left_anchor_track"): active_feature_names.append("Left Anchor Track")
    if neuro_config.get("narrow_column"): active_feature_names.append("Narrow Column Bound")

    max_workers = os.cpu_count() or 4
    print(f"\n{C_GREEN}[+] ALLOCATED {max_workers} PARALLEL CPU CORES{C_RESET}")

    for filename in selected_files:
        in_path = os.path.join(current_dir, filename)
        base, ext = os.path.splitext(filename)
        
        # Calculate non-overwriting incremental destination path
        out_path = get_unique_output_path(output_dir, base, ext)

        print(f"\n{C_CYAN}======================================================================{C_RESET}")
        print(f"{C_BOLD}TARGET FILE:{C_RESET} {filename}")

        doc = pymupdf.open(in_path)
        pdf_password = None
        if doc.is_encrypted:
            print(f"{C_RED}[!] ENCRYPTED PDF DETECTED. AUTHENTICATION REQUIRED.{C_RESET}")
            while True:
                pdf_password = input(f"{C_BOLD}ENTER PDF PASSWORD > {C_RESET}")
                if doc.authenticate(pdf_password):
                    print(f"{C_GREEN}[✓] DECRYPTION KEY ACCEPTED.{C_RESET}")
                    break
                print(f"{C_RED}[!] Incorrect password. Try again.{C_RESET}")

        total_pages = len(doc)
        doc.close()

        print(f"\n{C_CYAN}[>] PAGE RANGE CONFIGURATION (Total Pages: {total_pages}):{C_RESET}")
        range_input = input(f"{C_BOLD}SELECT PAGE RANGE [Press Enter for ALL {total_pages} Pages] > {C_RESET}").strip()
        target_pages = parse_page_range(range_input, total_pages)

        print(f"\n{C_YELLOW}[*] Processing all {len(target_pages)} pages in parallel...{C_RESET}\n")

        start_time = time.time()
        total_word_count = 0
        completed_count = 0

        temp_workspace = tempfile.mkdtemp(prefix="neuro_bionic_")

        tasks = []
        for p_idx in target_pages:
            temp_page_file = os.path.join(temp_workspace, f"page_{p_idx:05d}.pdf")
            tasks.append((in_path, p_idx, selected_fixation, selected_font_mode, neuro_config, pdf_password, temp_page_file))

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_single_page_isolated, t) for t in tasks]

            for future in as_completed(futures):
                p_idx, words = future.result()
                total_word_count += words
                completed_count += 1
                render_progress(
                    completed_count,
                    len(target_pages),
                    status=f"CONVERTED PAGE {p_idx + 1}/{total_pages}",
                )

        print("\n\n  " + f"{C_CYAN}[+] STITCHING FRAGMENTS INTO MASTER DOCUMENT...{C_RESET}")

        final_doc = pymupdf.open()
        for p_idx in target_pages:
            part_path = os.path.join(temp_workspace, f"page_{p_idx:05d}.pdf")
            part_doc = pymupdf.open(part_path)
            final_doc.insert_pdf(part_doc)
            part_doc.close()

        print(f"  {C_CYAN}[+] SERIALIZING ARTIFACT TO DISK...{C_RESET}")
        final_doc.save(out_path, deflate=True)
        final_doc.close()

        shutil.rmtree(temp_workspace, ignore_errors=True)

        elapsed = time.time() - start_time
        print(f"  {C_GREEN}[✓] SAVED TO ROUTER DIRECTORY -> {os.path.relpath(out_path, current_dir)}{C_RESET}")

        display_stats(total_word_count, len(target_pages), elapsed, active_feature_names)

    print(f"\n{C_GREEN}{C_BOLD}[✓] ALL PAGES CONVERTED SUCCESSFULLY.{C_RESET}")
    input(f"\n{C_DIM}Press ENTER to terminate session...{C_RESET}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{C_RED}{C_BOLD}[!] Process aborted by user. Exiting cleanly...{C_RESET}\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n{C_RED}[!] An unexpected error occurred: {e}{C_RESET}\n")
        sys.exit(1)