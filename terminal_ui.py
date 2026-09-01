import os
import sys

# ==========================================
# SCRIPT METADATA & OWNERSHIP
# ==========================================
SCRIPT_OWNER = "Phronesis"
VERSION = "9.2.0-NEURO-DIVERSE"

C_GREEN = "\033[92m"
C_CYAN = "\033[96m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_MAGENTA = "\033[95m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_RESET = "\033[0m"


def enable_windows_ansi():
    if os.name == "nt":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


def print_banner():
    os.system("cls" if os.name == "nt" else "clear")
    banner = f"""
{C_GREEN}======================================================================
  ██████╗ ██╗ ██████╗ ███╗   ██╗██╗ ██████╗    ██████╗ ██████╗ ███████╗
  ██╔══██╗██║██╔═══██╗████╗  ██║██║██╔════╝    ██╔══██╗██╔══██╗██╔════╝
  ██████╔╝██║██║   ██║██╔██╗ ██║██║██║         ██████╔╝██║  ██║█████╗  
  ██╔══██╗██║██║   ██║██║╚██╗██║██║██║         ██╔═══╝ ██║  ██║██╔══╝  
  ██████╔╝██║╚██████╔╝██║ ╚████║██║╚██████╗    ██║     ██████╔╝██║     
  ╚═════╝ ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝ ╚═════╝    ╚═╝     ╚═════╝ ╚═╝     
======================================================================
  [+] ENGINE CORE     : PARALLEL DYSLEXIA & ADHD TYPOGRAPHY PIPELINE
  [+] BUILD VERSION   : {VERSION}
  [+] SYSTEM OWNER    : {C_YELLOW}{SCRIPT_OWNER}{C_GREEN}
======================================================================{C_RESET}
"""
    print(banner)


def render_progress(current: int, total: int, bar_len: int = 28, status: str = ""):
    fraction = current / total if total > 0 else 1.0
    filled = int(bar_len * fraction)
    bar = f"{C_GREEN}#" * filled + f"{C_DIM}-" * (bar_len - filled) + f"{C_RESET}"
    percent = fraction * 100.0
    sys.stdout.write(
        f"\r  {C_CYAN}[MULTI_CORE_STREAM]{C_RESET} [{bar}] {C_BOLD}{percent:5.1f}%{C_RESET} | {C_YELLOW}{status:<32}{C_RESET}"
    )
    sys.stdout.flush()


def format_preview(sample_text: str, fixation: str, split_func) -> str:
    words = sample_text.split(" ")
    out = []
    for w in words:
        b, n = split_func(w, fixation=fixation)
        out.append(f"{C_BOLD}{C_GREEN}{b}{C_RESET}{n}")
    return " ".join(out)


def display_stats(total_words: int, page_count: int, elapsed_time: float, active_features: list):
    normal_minutes = total_words / 230.0
    bionic_minutes = total_words / 380.0
    time_saved = max(0.0, normal_minutes - bionic_minutes)

    print(f"\n{C_MAGENTA}================== COMPILATION & METRICS REPORT =================={C_RESET}")
    print(f"  {C_CYAN}[•] Pages Processed     :{C_RESET} {C_BOLD}{page_count}{C_RESET}")
    print(f"  {C_CYAN}[•] Words Enhanced      :{C_RESET} {C_BOLD}{total_words:,}{C_RESET} words")
    print(f"  {C_CYAN}[•] Total Render Time   :{C_RESET} {C_YELLOW}{elapsed_time:.2f} seconds{C_RESET}")
    print(f"  {C_CYAN}[•] Est. Normal Read    :{C_RESET} {normal_minutes:.1f} minutes")
    print(f"  {C_GREEN}[•] Est. Bionic Read    :{C_RESET} {C_BOLD}{bionic_minutes:.1f} minutes{C_RESET}")
    print(f"  {C_GREEN}[★] Time Saved (Boost)  :{C_RESET} {C_BOLD}{C_YELLOW}{time_saved:.1f} minutes (~40% boost){C_RESET}")

    if active_features:
        print(f"\n  {C_YELLOW}[+] Active Profiles     :{C_RESET} {C_CYAN}{', '.join(active_features)}{C_RESET}")
    print(f"{C_MAGENTA}=================================================================={C_RESET}")