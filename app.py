from __future__ import annotations
import sys
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from pdf_converter.image_pdf import images_to_pdf
from pdf_converter.merge import merge_pdfs
from pdf_converter.pdf_images import pdf_to_images
from pdf_converter.pdf_word import pdf_to_word
from pdf_converter.split import split_pdf
from pdf_converter.validation import ConversionError, open_pdf
from pdf_converter.word_pdf import libreoffice_path, word_to_pdf

st.set_page_config(page_title="Paperplane · PDF tools", page_icon="📄", layout="wide")
st.markdown("""
<style>
.stApp { background:#f6f7fb; color:#172033; } [data-testid="stHeader"] { background:transparent; }
[data-testid="stSidebar"] { background:#101a32; } [data-testid="stSidebar"] * { color:#eef2ff !important; }
h1,h2,h3 { font-family:ui-sans-serif,system-ui,-apple-system,sans-serif !important; letter-spacing:-.035em; }
.hero { background:linear-gradient(120deg,#172c51,#304c80 58%,#688bd1); border-radius:24px; padding:32px 38px; color:white; margin:8px 0 28px; box-shadow:0 16px 42px #24395b22; }
.hero h1 { color:white; font-size:2.35rem; margin:0 0 8px; } .hero p { color:#d9e5ff; margin:0; font-size:1.04rem; }
.muted { color:#758096; font-size:.92rem; } div.stButton > button[kind="primary"] { border-radius:12px; font-weight:700; min-height:46px; }
[data-testid="stFileUploader"] section { background:white; border:1px dashed #b7c3d8; border-radius:16px; }
.stDownloadButton button { border-radius:12px; font-weight:700; min-height:44px; }
</style>
""", unsafe_allow_html=True)

TOOLS = ["PDF to Images", "Images to PDF", "PDF to Word", "Word to PDF", "Merge PDFs", "Split PDF"]
st.sidebar.markdown("## 📄 Paperplane")
st.sidebar.caption("PRIVATE · DOCUMENT TOOLS")
tool = st.sidebar.radio("Choose a tool", TOOLS, label_visibility="collapsed")
st.sidebar.divider()
st.sidebar.markdown("**Processed by this service**")
st.sidebar.caption("Documents are processed by this Paperplane server without external conversion APIs. Temporary conversion files are cleaned up. Uploaded and generated content may remain in the active session's memory until the session expires.")
st.sidebar.caption("50 MB per file · 500 pages per PDF")
st.markdown('<div class="hero"><h1>Documents, in good hands.</h1><p>Six practical PDF tools, processed by this service without external conversion APIs.</p></div>', unsafe_allow_html=True)
intro = {
"PDF to Images": ("Turn PDF pages into images", "Export every page as a crisp PNG or JPG, bundled in one ZIP."),
"Images to PDF": ("Bring images together", "Combine JPG, PNG, WebP, BMP, or TIFF images into a single PDF."),
"PDF to Word": ("Make a PDF editable", "Create an editable Word document from a text based PDF. Complex layouts and scans may need cleanup; OCR is not included."),
"Word to PDF": ("Share a Word file as PDF", "Convert a DOCX document locally with LibreOffice."),
"Merge PDFs": ("Merge PDFs in order", "Combine two or more PDFs into one document."),
"Split PDF": ("Extract the pages you need", "Choose an inclusive page range and save it as a new PDF.")}
title, subtitle = intro[tool]
st.subheader(title)
st.markdown(f'<p class="muted">{subtitle}</p>', unsafe_allow_html=True)

def upload(label, types, multiple=False):
    return st.file_uploader(label, type=types, accept_multiple_files=multiple)
def describe(files):
    for f in files: st.caption(f"📎 {f.name} · {len(f.getvalue()) / 1024:.0f} KB")
def run_action(fn):
    try:
        with st.spinner("Working locally…"): return fn()
    except ConversionError as exc: st.error(str(exc))
    except Exception: st.error("Something went wrong while processing this file. Check that it is valid and try again.")
    return None

def _page_count(data):
    doc = open_pdf(data)
    try: return doc.page_count
    finally: doc.close()

if tool == "PDF to Images":
    f = upload("Choose a PDF", ["pdf"])
    if f:
        describe([f]); c1,c2 = st.columns(2)
        fmt = c1.selectbox("Image format", ["PNG", "JPG"]); dpi = c2.slider("Resolution (DPI)", 72, 300, 150, 12)
        if st.button("Convert pages", type="primary", disabled=not f):
            result = run_action(lambda: pdf_to_images(f.getvalue(), fmt, dpi))
            if result:
                data,count = result; st.success(f"Done · {count} pages converted")
                st.download_button("Download images (ZIP)", data, f"{Path(f.name).stem}-images.zip", "application/zip", type="primary")
elif tool == "Images to PDF":
    files = upload("Choose images (their upload order is preserved)", ["jpg","jpeg","png","webp","bmp","tif","tiff"], True)
    if files: describe(files)
    if st.button("Create PDF", type="primary", disabled=not files):
        result = run_action(lambda: images_to_pdf([f.getvalue() for f in files]))
        if result:
            st.success(f"Done · {len(files)} images combined")
            st.download_button("Download PDF", result, "images-combined.pdf", "application/pdf", type="primary")
elif tool == "PDF to Word":
    f = upload("Choose a PDF", ["pdf"])
    if f: describe([f])
    if st.button("Convert to Word", type="primary", disabled=not f):
        result = run_action(lambda: pdf_to_word(f.getvalue()))
        if result:
            st.success("Word document is ready")
            st.download_button("Download DOCX", result, f"{Path(f.name).stem}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", type="primary")
elif tool == "Word to PDF":
    if libreoffice_path(): st.info("LibreOffice detected · conversion runs on this server.")
    else: st.warning("LibreOffice is not installed. Install it to use this conversion.")
    f = upload("Choose a Word document", ["docx"])
    if f: describe([f])
    if st.button("Convert to PDF", type="primary", disabled=not f):
        result = run_action(lambda: word_to_pdf(f.getvalue()))
        if result:
            st.success("PDF is ready")
            st.download_button("Download PDF", result, f"{Path(f.name).stem}.pdf", "application/pdf", type="primary")
elif tool == "Merge PDFs":
    files = upload("Choose PDFs (selection order is merge order)", ["pdf"], True)
    if files: describe(files); st.caption("Merge order follows the order shown above.")
    if st.button("Merge PDFs", type="primary", disabled=not files or len(files) < 2):
        result = run_action(lambda: merge_pdfs([f.getvalue() for f in files]))
        if result:
            st.success("PDFs merged successfully")
            st.download_button("Download merged PDF", result, "merged.pdf", "application/pdf", type="primary")
elif tool == "Split PDF":
    f = upload("Choose a PDF", ["pdf"])
    if f:
        describe([f]); info = run_action(lambda: _page_count(f.getvalue()))
        if info:
            pages = info; st.info(f"This PDF has {pages} pages.")
            c1,c2 = st.columns(2)
            start = c1.number_input("Starting page", min_value=1, max_value=pages, value=1)
            end = c2.number_input("Ending page (inclusive)", min_value=1, max_value=pages, value=pages)
            if st.button("Extract pages", type="primary", disabled=start > end):
                result = run_action(lambda: split_pdf(f.getvalue(), int(start), int(end)))
                if result:
                    data,extracted = result; st.success(f"Done · {extracted} pages extracted")
                    st.download_button("Download extracted PDF", data, "extracted-pages.pdf", "application/pdf", type="primary")

st.divider()
st.caption("Paperplane processes uploads on the server hosting this app. No third-party conversion API is used; do not upload documents unless you trust the service operator.")
