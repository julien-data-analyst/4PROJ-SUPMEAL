import base64
import binascii

from django.core.exceptions import ValidationError

ALLOWED_IMAGE_MIME_TYPES = {"image/png", "image/jpeg", "image/svg+xml"}


def _sniff_mime_type(data: bytes) -> str | None:
    """Detects an image's actual type from its bytes, ignoring any
    client-supplied label - a data URI's declared MIME type is just text
    and trivially spoofable, so it can't be trusted on its own.
    """
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    head = data.lstrip()[:256].lower()
    if b"<svg" in head or b"<?xml" in head:
        return "image/svg+xml"
    return None


def validate_image_data_uri(value: str | None) -> None:
    """Validates that ``value`` is either blank/``None`` (both fields using
    this validator are optional) or a base64 data URI whose declared MIME
    type and sniffed magic bytes both resolve to PNG, JPEG or SVG.
    """
    if not value:
        return

    if not value.startswith("data:"):
        raise ValidationError("Image must be a data URI (data:<mime>;base64,...).")

    header, _, encoded = value.partition(",")
    if ";base64" not in header:
        raise ValidationError("Image data URI must be base64-encoded.")

    declared_mime = header.removeprefix("data:").split(";")[0]
    if declared_mime not in ALLOWED_IMAGE_MIME_TYPES:
        raise ValidationError(
            f"Unsupported image type '{declared_mime}'. Allowed types: PNG, JPEG, SVG."
        )

    try:
        decoded = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValidationError("Image data is not valid base64.") from exc

    sniffed_mime = _sniff_mime_type(decoded)
    if sniffed_mime != declared_mime:
        raise ValidationError(
            "Image content does not match its declared type. Allowed types: PNG, JPEG, SVG."
        )
