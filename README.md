# Paperplane — local PDF converter

A local-first Streamlit app for common PDF and image conversions. Documents are processed by Python on your Mac using local libraries; they are not sent to a conversion API. Streamlit sends uploads from the browser to the local Python server. The app binds to `127.0.0.1` by default and uses memory or temporary directories, which are removed after each conversion.

## Features

- PDF to PNG or JPG, adjustable 72–300 DPI, all pages in a ZIP.
- JPG, JPEG, PNG, WebP, BMP, and TIFF images to one PDF, preserving upload order and flattening transparency over white.
- PDF to editable DOCX using pdf2docx. Complex layouts may need corrections; scans are not OCR processed.
- DOCX to PDF through local LibreOffice headless mode.
- Merge two or more valid PDFs in displayed selection order.
- Extract an inclusive page range from a PDF.
- 50 MB per input file, 500 pages per PDF, 20 PDFs per merge, 100 images per image-to-PDF operation (100 MB combined image inputs), and a 200 MB output cap by default.

## Prerequisites

Use Python 3.11 or 3.12 (the pinned conversion libraries may not yet support newer Python releases). Install LibreOffice if you need Word to PDF. On macOS, download it from [libreoffice.org](https://www.libreoffice.org/download/download/) or use Homebrew: `brew install --cask libreoffice`.

## macOS setup

From this `pdf/` directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open <http://localhost:8501>. Streamlit binds to localhost by default. Keep the terminal open while using the app; press Control-C to stop it.

## Tests

```bash
source .venv/bin/activate
python -m pytest
```

Tests create their own sample PDFs and images. The DOCX-to-PDF integration test is skipped when LibreOffice is unavailable; missing-LibreOffice behavior is tested regardless.

## Limitations and troubleshooting

- PDF-to-Word recreates text and layout heuristically. Complex tables, columns, and scanned pages may not convert well. No OCR is implemented.
- Password-protected PDFs are rejected with a clear message; the app does not bypass document security.
- Animated image files use their first frame.
- If a conversion fails, verify the source opens normally and is within the file/page limits. For Word-to-PDF, confirm LibreOffice is installed and available as `libreoffice` or `soffice`, then restart Streamlit.
- Conversion libraries and PDFs can consume substantial memory. Keep within the stated limits for predictable processing.

## Configuration

The main limits are defined in `src/pdf_converter/__init__.py`. The app uses Streamlit's localhost default; do not add a public network bind when running with sensitive files. The interface uses local system fonts and does not request external assets.
