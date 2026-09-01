# ⚡ Bionic & Neuro-Accessible PDF Engine

[![License: Personal Use Only](https://img.shields.io/badge/License-Personal%20Use%20Only-red.svg)](#-license--terms-of-use)
[![AI Collaborator](https://img.shields.io/badge/Collaborator-Google%20Gemini-4285F4?style=flat&logo=google-gemini&logoColor=white)](https://gemini.google.com)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

A parallelized document conversion engine designed for enhanced reading velocity, ADHD visual anchoring, and Dyslexia reading comfort without altering document structure, diagrams, or images.

* **Creator & Maintainer:** [Phronesis](https://github.com/phronesis4)
* **Repository:** [phronesis4/bionic-pdf](https://github.com/phronesis4/bionic-pdf)
* **Version:** `9.2.0-NEURO-DIVERSE`

---

## ✨ Features at a Glance

* **Bionic Fixation (F1–F5):** Dynamic visual anchors ranging from F1 (~65% bold) down to F5 (1-letter minimal anchor).
* **Dyslexia Suite:** Bottom-weighted *OpenDyslexic* typography, anti-crowding letter spacing, word-gap expansion (+18%), and Irlen Syndrome background tints (Warm Cream, Pastel Mint, Sky Blue, Soft Peach).
* **ADHD Scanning Suite:** *Atkinson Hyperlegible* & *Lexend Fluency* typefaces, stop-word dimming (dimming *the, is, and* to soft slate), left-margin guide rails, and narrow column saccade bounds.
* **100% Vector & Table Protection:** Converts text inside tables and rotated headers (0°, 90°, 180°, 270°) while keeping borders, line grids, flowcharts, decision trees, and image layers untouched.
* **Zero Collision & Boundary Guards:** Exact baseline coordinate locking and adaptive optical-scale boundary guards prevent vertical line overlap and right-margin text clipping.
* **Multi-Core Parallel Streaming:** Distributes multi-hundred-page documents across all available CPU threads in isolated memory workers.
* **Non-Overwriting Export:** Automatically generates incremental output filenames (`doc_bionic_1.pdf`, `doc_bionic_2.pdf`) inside `./converted_bionic/`.

---

## ⚡ Accessibility Profiles

| Mode | Key | Preset Configuration |
|---|:---:|---|
| **My Preference** | `[P]` | Atkinson Hyperlegible + F3 (~40% Bold) + Micro Letter-Spacing + Left-Margin Anchor Track + Narrow Column Bound |
| **One-Click Dyslexia** | `[D]` | OpenDyslexic Font + F3 + Irlen Warm-Cream Tint + Word-Gap Expansion (+18%) + Anti-Crowding Letter-Spacing + Left Anchor Track |
| **One-Click ADHD** | `[A]` | Atkinson Hyperlegible + F3 + Stop-Word Dimming (Slate-Gray) + Left-Margin Anchor Track + Micro Letter-Spacing |
| **Custom Configuration** | `[C]` | Mix and match any font, fixation scale (F1–F5), and visual filter combination |

---

## 🛠️ Installation & Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/phronesis4/bionic-pdf.git
   cd bionic-pdf
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 How to Use

1. **Add Target Documents:**  
   Place the `.pdf` file(s) you want to convert directly inside the root `bionic-pdf/` folder.

2. **Run the Engine:**
   ```bash
   python main.py
   ```

3. **Select Options:**
   * Select your target document from the discovered file list.
   * Choose an operational profile (`P`, `D`, `A`, or `C`).
   * Select the page range (press **Enter** to convert all pages).

4. **Access Converted PDFs:**  
   Your processed files will be saved in the `./converted_bionic/` directory.

---

## 📦 Dependencies

* [PyMuPDF (`pymupdf >= 1.24.0`)](https://pymupdf.readthedocs.io/)
* [Pillow (`pillow >= 10.0.0`)](https://pillow.readthedocs.io/)

---

## 🤝 Acknowledgements & Contributions

* **[Phronesis](https://github.com/phronesis4)** — System Architecture, Feature Design & Project Maintainer
* **Google Gemini** — AI Pair Programmer & Code Optimization Assistant

---

## 📄 License & Terms of Use

Copyright (c) 2026 **Phronesis**. All rights reserved.

This repository is source-available for **personal, non-commercial use only**.

* **Allowed:** You may download, inspect, and run this software locally on your personal machine.
* **Prohibited:** You may **NOT** modify, adapt, alter, republish, redistribute, sublicense, sell, or mirror this source code (or any part of it) on GitHub or any other platform without explicit prior written consent from **Phronesis**.
