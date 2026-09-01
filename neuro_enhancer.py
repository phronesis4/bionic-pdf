import math
import os
import urllib.request
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*fitz.*")

import pymupdf

FONT_DIR = ".fonts"
os.makedirs(FONT_DIR, exist_ok=True)

# Free Open-Source Accessibility Fonts
FONT_URLS = {
    "opendyslexic_reg": "https://raw.githubusercontent.com/antijingoist/opendyslexic/master/compiled/OpenDyslexic-Regular.otf",
    "opendyslexic_bold": "https://raw.githubusercontent.com/antijingoist/opendyslexic/master/compiled/OpenDyslexic-Bold.otf",
    "opendyslexic_it": "https://raw.githubusercontent.com/antijingoist/opendyslexic/master/compiled/OpenDyslexic-Italic.otf",
    "atkinson_reg": "https://raw.githubusercontent.com/google/fonts/main/ofl/atkinsonhyperlegible/AtkinsonHyperlegible-Regular.ttf",
    "atkinson_bold": "https://raw.githubusercontent.com/google/fonts/main/ofl/atkinsonhyperlegible/AtkinsonHyperlegible-Bold.ttf",
    "atkinson_it": "https://raw.githubusercontent.com/google/fonts/main/ofl/atkinsonhyperlegible/AtkinsonHyperlegible-Italic.ttf",
    "lexend_reg": "https://raw.githubusercontent.com/googlefonts/lexend/main/fonts/lexend/ttf/Lexend-Regular.ttf",
    "lexend_bold": "https://raw.githubusercontent.com/googlefonts/lexend/main/fonts/lexend/ttf/Lexend-Bold.ttf",
}

# Base optical size compensation factors for wide dyslexia typefaces
FONT_SCALE_COMPENSATION = {
    "opendyslexic": 0.80,  # OpenDyslexic is ~25% wider than standard Helvetica
    "atkinson": 0.94,
    "lexend": 0.94,
    "bionic_sans": 1.00,
    "serif": 1.00,
    "mono": 0.90,
}

# Irlen Syndrome / Dyslexia Visual Stress Background Tint Palettes (RGB 0.0 - 1.0)
IRLEN_TINTS = {
    "cream": (0.976, 0.957, 0.910),     # #FAF4E8 Warm Matte Cream
    "mint": (0.922, 0.961, 0.933),      # #EBF5EE Soft Pastel Mint
    "blue": (0.918, 0.949, 0.973),      # #EAF2F8 Calming Sky Tint
    "peach": (0.992, 0.941, 0.902),     # #FDF0E6 Soft Peach
    "none": None,
}

STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "be",
    "been", "being", "in", "on", "at", "to", "for", "of", "with", "by",
    "from", "up", "about", "into", "over", "after", "that", "this", "these",
    "those", "it", "its", "as", "if", "then", "than", "such", "which", "no", "not"
}

UNICODE_REPLACEMENTS = {
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u2022": "*", "\u00a0": " ",
    "\u200b": "", "\u202f": " ", "\u2009": " ",
}

_LOCAL_FONT_CACHE = {}


def sanitize_text(text: str) -> str:
    for orig, rep in UNICODE_REPLACEMENTS.items():
        text = text.replace(orig, rep)
    return text


def ensure_font_downloaded(key: str) -> str:
    if key not in FONT_URLS:
        return ""
    url = FONT_URLS[key]
    ext = ".otf" if "opendyslexic" in key else ".ttf"
    local_path = os.path.join(FONT_DIR, f"{key}{ext}")

    if not os.path.exists(local_path):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as response, open(local_path, "wb") as out_file:
                out_file.write(response.read())
        except Exception:
            return ""
    return local_path


def measure_text_width(text: str, fontname: str, fontfile: str, fontsize: float) -> float:
    if not text:
        return 0.0
    if fontfile and os.path.exists(fontfile):
        if fontfile not in _LOCAL_FONT_CACHE:
            _LOCAL_FONT_CACHE[fontfile] = pymupdf.Font(fontfile=fontfile)
        return _LOCAL_FONT_CACHE[fontfile].text_length(text, fontsize=fontsize)
    return pymupdf.get_text_length(text, fontname=fontname, fontsize=fontsize)


def bionic_word_split(word: str, fixation: str = "F3") -> tuple[str, str]:
    clean_word = word.strip(".,!?;:\"')]}*·•[]()<>{}-")
    word_len = len(clean_word)

    if word_len == 0:
        return "", word

    # Keep standalone numbers and reference tags intact
    if clean_word.replace(".", "").replace("-", "").isdigit():
        return word, ""

    fixation_ratios = {"F1": 0.65, "F2": 0.50, "F3": 0.40, "F4": 0.30, "F5": 0.15}
    ratio = fixation_ratios.get(fixation.upper(), 0.40)

    if fixation.upper() == "F5":
        fix_len = 1
    elif word_len == 1:
        fix_len = 1
    elif word_len <= 3:
        fix_len = 2 if fixation.upper() in ["F1", "F2"] and word_len == 3 else 1
    else:
        fix_len = math.ceil(word_len * ratio)

    if word_len > 3 and fix_len >= word_len:
        fix_len = word_len - 1

    leading_punct = len(word) - len(word.lstrip(".,!?;:\"')]}*·•[]()<>{}-"))
    split_idx = leading_punct + fix_len

    return word[:split_idx], word[split_idx:]


def resolve_font_resources(font_mode: str, is_italic: bool) -> tuple[str, str, str, str]:
    if font_mode == "opendyslexic":
        b_file = ensure_font_downloaded("opendyslexic_bold")
        n_file = ensure_font_downloaded("opendyslexic_it" if is_italic else "opendyslexic_reg")
        if b_file and n_file:
            return "dyslexic_b", "dyslexic_n", b_file, n_file
    elif font_mode == "atkinson":
        b_file = ensure_font_downloaded("atkinson_bold")
        n_file = ensure_font_downloaded("atkinson_it" if is_italic else "atkinson_reg")
        if b_file and n_file:
            return "atkinson_b", "atkinson_n", b_file, n_file
    elif font_mode == "lexend":
        b_file = ensure_font_downloaded("lexend_bold")
        n_file = ensure_font_downloaded("lexend_reg")
        if b_file and n_file:
            return "lexend_b", "lexend_n", b_file, n_file

    if font_mode == "serif":
        return ("tibi", "tiit", "", "") if is_italic else ("tibo", "tiro", "", "")
    elif font_mode == "mono":
        return ("cobi", "coit", "", "") if is_italic else ("cobo", "cour", "", "")
    else:
        return ("hebi", "heit", "", "") if is_italic else ("hebo", "helv", "", "")