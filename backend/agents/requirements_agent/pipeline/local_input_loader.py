"""Local input loading helpers for Requirements Agent finish runs."""

from __future__ import annotations

import csv
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.agents.requirements_agent.pipeline.validation_runner import extract_project_fields

JsonObject = dict[str, Any]

REQUIREMENTS_AGENT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = Path(__file__).resolve().parents[4]


def _default_prd_path() -> Path:
    agents_dir = WORKSPACE_ROOT / "backend" / "agents"
    for candidate in sorted(
        agents_dir.glob("requirements_agent_*/PRD/PRD_001_notification_center.pdf")
    ):
        return candidate
    return REQUIREMENTS_AGENT_ROOT / "local_inputs" / "PRD_001_notification_center.pdf"


DEFAULT_PRD_PATH = _default_prd_path()
DEFAULT_EMPLOYEE_DATA_DIR = WORKSPACE_ROOT / "datasets" / "raw"

SOURCE_CSV_FILES = {
    "employee": Path("hr") / "employee_dummy_100.csv",
    "github_activity": Path("github") / "github_activity_dummy_100.csv",
    "slack_activity": Path("slack") / "slack_activity_dummy_100.csv",
    "jira_activity": Path("jira") / "jira_activity_dummy_100.csv",
    "calendar_activity": Path("calendar") / "google_calendar_activity_dummy_100.csv",
}


class LocalInputError(RuntimeError):
    """Raised when local finish-run inputs cannot be loaded."""


class PDFTextExtractionError(LocalInputError):
    """Raised when a PDF cannot be converted to raw text locally."""


@dataclass(frozen=True)
class LocalPRDInput:
    """PRD text and source metadata for local runner execution."""

    raw_text: str
    document_id: str
    document_type: str
    source_uri: str
    raw_text_ref: str
    extraction: JsonObject

    def as_pipeline_kwargs(self) -> JsonObject:
        return {
            "raw_text": self.raw_text,
            "document_id": self.document_id,
            "document_type": self.document_type,
            "source_uri": self.source_uri,
        }


def load_local_prd_input(
    prd_path: str | Path = DEFAULT_PRD_PATH,
    *,
    document_id: str | None = None,
) -> LocalPRDInput:
    """Load a local PRD PDF/text/markdown/json file without summarizing it."""

    path = Path(prd_path)
    if not path.exists():
        raise LocalInputError(f"PRD input does not exist: {path}")
    if not path.is_file():
        raise LocalInputError(f"PRD input must be a file: {path}")

    suffix = path.suffix.casefold()
    extraction: JsonObject = {"source_format": suffix.lstrip(".") or "unknown"}
    if suffix == ".pdf":
        raw_text, pdf_meta = extract_pdf_text(path)
        extraction.update(pdf_meta)
    elif suffix in {".md", ".txt"}:
        raw_text = path.read_text(encoding="utf-8")
        extraction.update({"method": "plain_text", "page_count": None})
    elif suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw_text = _raw_text_from_json(payload)
        extraction.update({"method": "json_raw_text", "page_count": None})
    else:
        raise LocalInputError(
            f"Unsupported PRD input format '{path.suffix}'. Use pdf, md, txt, or json."
        )

    if not raw_text.strip():
        raise LocalInputError(f"PRD input produced empty raw text: {path}")

    resolved = path.resolve()
    doc_id = document_id or _document_id_from_path(path)
    return LocalPRDInput(
        raw_text=raw_text,
        document_id=doc_id,
        document_type="prd",
        source_uri=resolved.as_uri(),
        raw_text_ref=f"{resolved.as_uri()}#raw_text",
        extraction=extraction,
    )


def extract_pdf_text(pdf_path: str | Path) -> tuple[str, JsonObject]:
    """Extract text from a PDF using an installed local reader library.

    The project intentionally does not do OCR here. If the PDF is image-only,
    this returns a clear error so the finish run can decide whether to add an
    OCR step or request a text PRD copy.
    """

    path = Path(pdf_path)
    attempted: list[str] = []
    for method_name, extractor in (
        ("pypdf", _extract_with_pypdf),
        ("PyPDF2", _extract_with_pypdf2),
        ("pdfplumber", _extract_with_pdfplumber),
    ):
        attempted.append(method_name)
        try:
            text, page_count = extractor(path)
        except ModuleNotFoundError:
            continue
        except Exception as exc:  # pragma: no cover - depends on optional PDF readers.
            raise PDFTextExtractionError(
                f"PDF text extraction failed with {method_name}: {exc}"
            ) from exc
        if text.strip():
            return text, {
                "method": method_name,
                "page_count": page_count,
                "ocr_performed": False,
                "ocr_required": False,
            }
        raise PDFTextExtractionError(
            f"PDF text extraction with {method_name} returned empty text. OCR may be required."
        )

    raise PDFTextExtractionError(
        "No local PDF text reader is installed. Install pypdf, PyPDF2, or pdfplumber, "
        f"then retry. Attempted readers: {', '.join(attempted)}."
    )


def read_employee_data_headers(
    employee_data_dir: str | Path = DEFAULT_EMPLOYEE_DATA_DIR,
) -> JsonObject:
    """Read source CSV headers from datasets/raw without inspecting row values."""

    root = Path(employee_data_dir)
    if not root.exists():
        raise LocalInputError(f"Employee data directory does not exist: {root}")
    result: JsonObject = {}
    for source, relative_path in SOURCE_CSV_FILES.items():
        csv_path = root / relative_path
        if not csv_path.exists():
            raise LocalInputError(f"Missing CSV source for {source}: {csv_path}")
        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration as exc:
                raise LocalInputError(f"CSV source has no header row: {csv_path}") from exc
        columns = [column.strip().lstrip("\ufeff") for column in header if column.strip()]
        result[source] = {
            "path": str(csv_path),
            "columns": columns,
            "column_count": len(columns),
        }
    return result


def validate_employee_column_rules_against_headers(
    employee_column_rules: Mapping[str, Any],
    source_headers: Mapping[str, Any],
) -> JsonObject:
    """Check that configured rule columns exist in the local CSV headers."""

    missing_columns: list[JsonObject] = []
    unknown_sources: list[JsonObject] = []
    checked_columns: list[str] = []

    for rule_key, rule in employee_column_rules.get("requirement_type_rules", {}).items():
        for column in rule.get("columns", []):
            source = str(column.get("source", ""))
            name = str(column.get("name", ""))
            column_key = f"{source}.{name}" if source and name else ""
            if not source or not name:
                missing_columns.append(
                    {
                        "rule_key": rule_key,
                        "source": source,
                        "name": name,
                        "column_key": column_key,
                        "reason": "Rule column must include both source and name.",
                    }
                )
                continue
            if source not in source_headers:
                unknown_sources.append(
                    {
                        "rule_key": rule_key,
                        "source": source,
                        "name": name,
                        "column_key": column_key,
                        "reason": "Rule references a CSV source that is not loaded.",
                    }
                )
                continue
            checked_columns.append(column_key)
            columns = set(source_headers[source].get("columns", []))
            if name not in columns:
                missing_columns.append(
                    {
                        "rule_key": rule_key,
                        "source": source,
                        "name": name,
                        "column_key": column_key,
                        "reason": "Rule references a column missing from local CSV headers.",
                    }
                )

    status = "passed" if not missing_columns and not unknown_sources else "failed"
    return {
        "status": status,
        "checked_column_count": len(set(checked_columns)),
        "missing_required_columns": missing_columns,
        "unknown_sources": unknown_sources,
        "source_headers": dict(source_headers),
    }


def build_local_project_fields(raw_text: str) -> JsonObject:
    """Infer project fields from PRD raw text for local finish runs."""

    return extract_project_fields(raw_text)


def _extract_with_pypdf(path: Path) -> tuple[str, int | None]:
    import pypdf

    reader = pypdf.PdfReader(str(path))
    pages = list(reader.pages)
    text = "\n\n".join(page.extract_text() or "" for page in pages)
    return text, len(pages)


def _extract_with_pypdf2(path: Path) -> tuple[str, int | None]:
    import PyPDF2

    reader = PyPDF2.PdfReader(str(path))
    pages = list(reader.pages)
    text = "\n\n".join(page.extract_text() or "" for page in pages)
    return text, len(pages)


def _extract_with_pdfplumber(path: Path) -> tuple[str, int | None]:
    import pdfplumber

    with pdfplumber.open(str(path)) as pdf:
        pages = list(pdf.pages)
        text = "\n\n".join(page.extract_text() or "" for page in pages)
    return text, len(pages)


def _raw_text_from_json(payload: Any) -> str:
    if isinstance(payload, str):
        return payload
    if not isinstance(payload, Mapping):
        raise LocalInputError("JSON PRD input must be a string or object with raw text.")
    for key in ("raw_text", "text", "content", "prd_text"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    raise LocalInputError("JSON PRD input must include one of raw_text, text, content, prd_text.")


def _document_id_from_path(path: Path) -> str:
    stem = path.stem.casefold()
    cleaned = re.sub(r"[^a-z0-9]+", "_", stem).strip("_")
    return cleaned or "prd_document"
