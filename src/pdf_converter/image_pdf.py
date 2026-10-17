"""Combine images into a PDF, preserving the submitted order."""
from io import BytesIO

from PIL import Image, ImageOps

from . import MAX_OUTPUT_BYTES
from .validation import image_bytes, image_format, ConversionError


def images_to_pdf(images: list[bytes]) -> bytes:
    if not images:
        raise ConversionError("Upload at least one image.")
    if len(images) > 100:
        raise ConversionError("You can combine up to 100 images at a time.")
    if sum(len(item.getvalue()) if hasattr(item, "getvalue") else len(item) for item in images) > 100 * 1024 * 1024:
        raise ConversionError("Combined image inputs exceed the 100 MB total limit.")
    pages = []
    try:
        for raw in images:
            data = image_bytes(raw)
            image_format(data)
            with Image.open(BytesIO(data)) as original:
                img = ImageOps.exif_transpose(original)
                if getattr(img, "n_frames", 1) > 1:
                    img.seek(0)
                if img.mode in ("RGBA", "LA") or "transparency" in img.info:
                    rgba = img.convert("RGBA")
                    white = Image.new("RGB", rgba.size, "white")
                    white.paste(rgba, mask=rgba.getchannel("A"))
                    pages.append(white)
                else:
                    pages.append(img.convert("RGB"))
        result = BytesIO()
        pages[0].save(result, format="PDF", save_all=True, append_images=pages[1:])
        payload = result.getvalue()
        if len(payload) > MAX_OUTPUT_BYTES:
            raise ConversionError("The resulting PDF exceeds the 200 MB output limit.")
        return payload
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError("One or more images could not be combined.") from exc
    finally:
        for page in pages:
            page.close()
