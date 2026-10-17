from io import BytesIO
import zipfile

import fitz
import pytest
from PIL import Image

from pdf_converter.validation import ConversionError, open_pdf
from pdf_converter.image_pdf import images_to_pdf
from pdf_converter.pdf_images import pdf_to_images
from pdf_converter.merge import merge_pdfs
from pdf_converter.split import split_pdf
from pdf_converter.pdf_word import pdf_to_word
from pdf_converter.word_pdf import libreoffice_path, word_to_pdf


def make_pdf(*labels):
    doc = fitz.open()
    for label in labels:
        page = doc.new_page()
        page.insert_text((72, 72), label)
    data = doc.tobytes()
    doc.close()
    return data


def make_image(color, mode="RGB"):
    im = Image.new(mode, (40, 30), color)
    out = BytesIO()
    im.save(out, "PNG")
    im.close()
    return out.getvalue()


def test_pdf_validation():
    doc = open_pdf(make_pdf("ok"))
    assert doc.page_count == 1
    doc.close()
    for bad in (b"", b"not a pdf"):
        with pytest.raises(ConversionError):
            open_pdf(bad)


def test_image_pdf_and_render():
    converted = images_to_pdf([make_image((255, 0, 0)), make_image((0, 255, 0, 128), "RGBA")])
    doc = fitz.open(stream=converted, filetype="pdf")
    assert doc.page_count == 2
    doc.close()
    archive, count = pdf_to_images(converted, "PNG", 100)
    assert count == 2
    with zipfile.ZipFile(BytesIO(archive)) as zf:
        assert zf.namelist() == ["page-001.png", "page-002.png"]


def test_pdf_to_jpg_and_bad_image():
    archive, count = pdf_to_images(make_pdf("x"), "JPG", 72)
    assert count == 1
    with zipfile.ZipFile(BytesIO(archive)) as zf:
        assert zf.namelist()[0].endswith(".jpg")
    with pytest.raises(ConversionError):
        images_to_pdf([b"bad"])


def test_merge_order_and_split_inclusive_range():
    merged = merge_pdfs([make_pdf("first"), make_pdf("second", "third")])
    doc = fitz.open(stream=merged, filetype="pdf")
    assert [p.get_text().strip() for p in doc] == ["first", "second", "third"]
    doc.close()
    extracted, count = split_pdf(merged, 2, 3)
    result = fitz.open(stream=extracted, filetype="pdf")
    assert count == 2 and [p.get_text().strip() for p in result] == ["second", "third"]
    result.close()
    with pytest.raises(ConversionError):
        split_pdf(merged, 0, 3)
    with pytest.raises(ConversionError):
        merge_pdfs([b"not pdf", make_pdf("ok")])


def test_pdf_to_docx_and_temp_cleanup(tmp_path, monkeypatch):
    import tempfile
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    payload = pdf_to_word(make_pdf("A simple heading", "A paragraph."))
    assert payload[:2] == b"PK"
    assert list(tmp_path.iterdir()) == []


def test_missing_libreoffice_is_handled(monkeypatch):
    monkeypatch.setattr("pdf_converter.word_pdf.libreoffice_path", lambda: None)
    with pytest.raises(ConversionError, match="LibreOffice was not found"):
        word_to_pdf(b"not empty")


@pytest.mark.skipif(not libreoffice_path(), reason="LibreOffice is not installed")
def test_word_to_pdf_when_libreoffice_available():
    from docx import Document
    source = BytesIO()
    doc = Document()
    doc.add_paragraph("Hello from a local test")
    doc.save(source)
    result = word_to_pdf(source.getvalue())
    assert result.startswith(b"%PDF-")
