from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from io import BytesIO
from typing import Any

from pypdf import PdfReader

MAX_PRD_UPLOAD_BYTES = 5 * 1024 * 1024
MIN_EXTRACTED_TEXT_CHARS = 40


class PrdFileParseError(ValueError):
    pass


@dataclass(frozen=True)
class ParsedPrdFile:
    text: str
    file_name: str
    content_type: str
    page_count: int | None
    byte_size: int


def parse_prd_file_upload(payload: dict[str, Any]) -> ParsedPrdFile:
    file_name = _required_string(payload.get("fileName"), "fileName")
    content_type = _string_or_default(payload.get("contentType"), "application/pdf")
    encoded_file = _required_string(payload.get("fileBase64"), "fileBase64")

    if content_type != "application/pdf" and not file_name.lower().endswith(".pdf"):
        raise PrdFileParseError("Only PDF PRD files are supported.")

    try:
        file_bytes = base64.b64decode(encoded_file, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise PrdFileParseError("Uploaded PRD file is not valid base64.") from exc

    if not file_bytes:
        raise PrdFileParseError("Uploaded PRD file is empty.")
    if len(file_bytes) > MAX_PRD_UPLOAD_BYTES:
        raise PrdFileParseError("Uploaded PRD file is too large. Max size is 5 MB.")

    text, page_count = extract_pdf_text(file_bytes)
    normalized_text = _normalize_text(text)
    if len(normalized_text) < MIN_EXTRACTED_TEXT_CHARS:
        raise PrdFileParseError(
            "Could not extract enough text from the PDF. Scanned/image PDFs are not supported yet."
        )

    return ParsedPrdFile(
        text=normalized_text,
        file_name=file_name,
        content_type=content_type,
        page_count=page_count,
        byte_size=len(file_bytes),
    )


def extract_pdf_text(file_bytes: bytes) -> tuple[str, int | None]:
    try:
        reader = PdfReader(BytesIO(file_bytes))
        pages = list(reader.pages)
        text = "\n\n".join(page.extract_text() or "" for page in pages)
    except Exception as exc:
        raise PrdFileParseError("Could not read the uploaded PDF.") from exc
    return text, len(pages)


def _required_string(value: Any, field_name: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    raise PrdFileParseError(f"{field_name} is required.")


def _string_or_default(value: Any, default: str) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else default


def _normalize_text(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(lines).strip()
