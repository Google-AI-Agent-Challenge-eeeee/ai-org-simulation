"""End-to-end orchestration for Requirements Agent.

The pipeline returns structured in-memory outputs by default. JSON files in
outputs/ are written only when explicitly requested by the caller.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypeVar

from backend.agents.requirements_agent.modules.column_selection_draft import (
    select_columns_draft,
)
from backend.agents.requirements_agent.modules.column_weighting_final import (
    calculate_column_weights,
)
from backend.agents.requirements_agent.modules.coverage_check import check_coverage
from backend.agents.requirements_agent.modules.human_confirm import (
    build_human_confirm_result,
    merge_project_specific_mapping,
)
from backend.agents.requirements_agent.modules.requirements_list_builder import (
    build_requirements_list,
    ensure_valid_requirements_list,
)
from backend.agents.requirements_agent.modules.taxonomy_matcher import (
    load_json,
    match_requirements,
)
from backend.agents.requirements_agent.pipeline.extraction_runner import (
    SectionExtractor,
    run_section_extraction,
)
from backend.agents.requirements_agent.pipeline.section_splitter import (
    prepare_document_sections,
)
from backend.agents.requirements_agent.pipeline.token_limit_verify import (
    DEFAULT_HARD_TOKEN_LIMIT,
    DEFAULT_RECOMMENDED_TOKEN_LIMIT,
)
from backend.agents.requirements_agent.pipeline.validation_runner import (
    Validator,
    run_validation,
)

JsonObject = dict[str, Any]
ProgressLogger = Callable[[str, Mapping[str, Any]], None]
T = TypeVar("T")

REQUIREMENTS_AGENT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCE_DIR = REQUIREMENTS_AGENT_ROOT / "references"
DEFAULT_SCHEMA_DIR = REQUIREMENTS_AGENT_ROOT / "schemas"
DEFAULT_OUTPUT_DIR = REQUIREMENTS_AGENT_ROOT / "outputs"

OUTPUT_FILENAMES = {
    "cleaned_prd_text": "Cleaned_PRD_Text.json",
    "section_extraction_result": "Section_Extraction_Result.json",
    "extracted_requirements_draft": "Extracted_Requirements_Draft.json",
    "mapped_requirements": "Mapped_Requirements.json",
    "column_selection_draft": "Column_Selection_Draft.json",
    "validation_result": "Validation_Result.json",
    "coverage_check_result": "Coverage_Check_Result.json",
    "human_confirm_result": "Human_Confirm_Result.json",
    "column_weighting_result": "Column_Weighting_Result.json",
    "requirements_list": "Requirements_List.json",
}


@dataclass(frozen=True)
class RequirementsPipelineConfig:
    """Runtime paths and gates for Requirements Agent."""

    reference_dir: Path = DEFAULT_REFERENCE_DIR
    schema_dir: Path = DEFAULT_SCHEMA_DIR
    output_dir: Path = DEFAULT_OUTPUT_DIR
    recommended_token_limit: int = DEFAULT_RECOMMENDED_TOKEN_LIMIT
    hard_token_limit: int = DEFAULT_HARD_TOKEN_LIMIT
    human_confirm_complete: bool = False
    write_outputs: bool = False
    progress_logger: ProgressLogger | None = None


def run_requirements_pipeline(
    raw_text: str,
    *,
    document_id: str = "prd_document",
    document_type: str = "prd",
    source_uri: str | None = None,
    project_id: str | None = None,
    project_fields: dict[str, Any] | None = None,
    project_specific_mapping: dict[str, str] | None = None,
    human_confirm_decisions: dict[str, Any] | None = None,
    extractor: SectionExtractor | None = None,
    validator: Validator | None = None,
    config: RequirementsPipelineConfig | None = None,
) -> JsonObject:
    """Run the Requirements Agent pipeline from raw PRD text to final list."""

    config = config or RequirementsPipelineConfig()
    progress_logger = config.progress_logger
    pipeline_started_at = time.perf_counter()
    _log_progress(
        progress_logger,
        "pipeline_start",
        document_id=document_id,
        raw_text_length=len(raw_text),
        write_outputs=config.write_outputs,
    )
    references = _run_stage(
        "load_references",
        progress_logger,
        lambda: load_references(config.reference_dir),
        reference_dir=str(config.reference_dir),
    )
    schemas = _run_stage(
        "load_schemas",
        progress_logger,
        lambda: load_schemas(config.schema_dir),
        schema_dir=str(config.schema_dir),
    )
    effective_project_specific_mapping = _run_stage(
        "merge_project_specific_mapping",
        progress_logger,
        lambda: merge_project_specific_mapping(project_specific_mapping, human_confirm_decisions),
    )

    prepared_document = _run_stage(
        "prepare_document_sections",
        progress_logger,
        lambda: prepare_document_sections(
            raw_text,
            document_id=document_id,
            document_type=document_type,
            source_uri=source_uri,
            recommended_limit=config.recommended_token_limit,
            hard_limit=config.hard_token_limit,
        ),
    )
    _log_progress(
        progress_logger,
        "document_sections_ready",
        section_count=len(prepared_document.get("sections", [])),
        token_check_statuses=_token_check_statuses(prepared_document),
    )
    extracted_draft = _run_stage(
        "run_section_extraction",
        progress_logger,
        lambda: run_section_extraction(
            prepared_document,
            extractor=extractor,
            rulebase=references["rulebase"],
            project_id=project_id,
            progress_logger=progress_logger,
        ),
        section_count=len(prepared_document.get("sections", [])),
    )
    mapped_requirements = _run_stage(
        "match_requirements",
        progress_logger,
        lambda: match_requirements(
            extracted_draft,
            references["taxonomy"],
            references["rulebase"],
            project_specific_mapping=effective_project_specific_mapping,
            mapped_requirements_id="mapped_requirements",
        ),
        candidate_count=len(extracted_draft.get("merged_requirement_candidates", [])),
    )
    column_selection = _run_stage(
        "select_columns_draft",
        progress_logger,
        lambda: select_columns_draft(
            mapped_requirements,
            references["employee_column_rules"],
            draft_id="column_selection_draft",
        ),
    )
    coverage_result = _run_stage(
        "check_coverage",
        progress_logger,
        lambda: check_coverage(
            prepared_document["sections"],
            mapped_requirements=mapped_requirements,
            extracted_requirements_draft=extracted_draft,
        ),
    )
    validation_result = _run_stage(
        "run_validation",
        progress_logger,
        lambda: run_validation(
            prepared_document=prepared_document,
            extracted_requirements_draft=extracted_draft,
            mapped_requirements=mapped_requirements,
            coverage_check=coverage_result,
            project_fields=project_fields,
            validator=validator,
        ),
    )
    human_confirm_result = _run_stage(
        "build_human_confirm_result",
        progress_logger,
        lambda: build_human_confirm_result(
            validation_result=validation_result,
            mapped_requirements=mapped_requirements,
            column_selection_draft=column_selection,
            human_confirm_complete=config.human_confirm_complete,
            human_confirm_decisions=human_confirm_decisions,
            project_specific_mapping=effective_project_specific_mapping,
        ),
        human_confirm_complete=config.human_confirm_complete,
    )
    applied_outputs = human_confirm_result["applied"]
    mapped_requirements_for_final = applied_outputs["mapped_requirements"]
    validation_result_for_final = applied_outputs["validation_result"]
    column_selection_for_final = applied_outputs["column_selection_draft"]
    column_weighting = _run_stage(
        "calculate_column_weights",
        progress_logger,
        lambda: calculate_column_weights(
            column_selection_for_final,
            references["employee_column_rules"],
            human_confirm_complete=human_confirm_result["human_confirm_complete"],
            weighting_id="column_weighting_result",
        ),
    )
    requirements_list = _run_stage(
        "build_requirements_list",
        progress_logger,
        lambda: build_requirements_list(
            mapped_requirements=mapped_requirements_for_final,
            column_selection_draft=column_selection_for_final,
            column_weighting_result=column_weighting,
            coverage_check=coverage_result,
            project_fields=validation_result_for_final.get("project_fields", {}),
            validation_result=validation_result_for_final,
            requirements_list_id="requirements_list",
        ),
    )
    _run_stage(
        "ensure_valid_requirements_list",
        progress_logger,
        lambda: ensure_valid_requirements_list(
            requirements_list,
            schemas.get("requirements_schema"),
        ),
    )

    outputs = {
        "cleaned_prd_text": prepared_document,
        "section_extraction_result": {
            "document": prepared_document["document"],
            "sections": prepared_document["sections"],
            "section_results": extracted_draft["section_results"],
        },
        "extracted_requirements_draft": extracted_draft,
        "mapped_requirements": mapped_requirements,
        "column_selection_draft": column_selection,
        "validation_result": validation_result_for_final,
        "coverage_check_result": coverage_result,
        "human_confirm_result": human_confirm_result,
        "column_weighting_result": column_weighting,
        "requirements_list": requirements_list,
    }
    result = {
        "_meta": {
            "pipeline_phase": "requirements_pipeline",
            "status": requirements_list.get("_meta", {}).get("status", "draft"),
            "write_outputs": config.write_outputs,
            "output_dir": str(config.output_dir),
        },
        "outputs": outputs,
    }
    if config.write_outputs:
        result["written_files"] = _run_stage(
            "write_pipeline_outputs",
            progress_logger,
            lambda: write_pipeline_outputs(outputs, config.output_dir),
            output_dir=str(config.output_dir),
        )
    _log_progress(
        progress_logger,
        "pipeline_done",
        status=result["_meta"]["status"],
        elapsed_seconds=round(time.perf_counter() - pipeline_started_at, 2),
    )
    return result


def _run_stage(
    stage: str,
    progress_logger: ProgressLogger | None,
    fn: Callable[[], T],
    **details: Any,
) -> T:
    started_at = time.perf_counter()
    _log_progress(progress_logger, "stage_start", stage=stage, **details)
    try:
        result = fn()
    except Exception as exc:
        _log_progress(
            progress_logger,
            "stage_failed",
            stage=stage,
            elapsed_seconds=round(time.perf_counter() - started_at, 2),
            error=type(exc).__name__,
        )
        raise
    _log_progress(
        progress_logger,
        "stage_done",
        stage=stage,
        elapsed_seconds=round(time.perf_counter() - started_at, 2),
    )
    return result


def _log_progress(
    progress_logger: ProgressLogger | None,
    event: str,
    **details: Any,
) -> None:
    if progress_logger is None:
        return
    progress_logger(event, details)


def _token_check_statuses(prepared_document: Mapping[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for token_check in prepared_document.get("token_checks", []):
        status = str(token_check.get("budget_status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
    return counts


def load_references(reference_dir: str | Path = DEFAULT_REFERENCE_DIR) -> JsonObject:
    """Load Phase 1 references."""

    reference_dir = Path(reference_dir)
    return {
        "taxonomy": load_json(reference_dir / "taxonomy.json"),
        "rulebase": load_json(reference_dir / "rulebase.json"),
        "employee_column_rules": load_json(reference_dir / "employee_column_rules.json"),
    }


def load_schemas(schema_dir: str | Path = DEFAULT_SCHEMA_DIR) -> JsonObject:
    """Load Phase 2 schemas for lightweight contract checks."""

    schema_dir = Path(schema_dir)
    return {
        "requirements_schema": load_json(schema_dir / "requirements_schema.json"),
        "extracted_requirements_draft_schema": load_json(
            schema_dir / "extracted_requirements_draft_schema.json"
        ),
        "mapped_requirements_schema": load_json(schema_dir / "mapped_requirements_schema.json"),
    }


def write_pipeline_outputs(
    outputs: Mapping[str, Any],
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> list[str]:
    """Write pipeline outputs to outputs/*.json when explicitly requested."""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written_files = []
    for output_key, filename in OUTPUT_FILENAMES.items():
        path = output_dir / filename
        with path.open("w", encoding="utf-8") as f:
            json.dump(outputs[output_key], f, ensure_ascii=False, indent=2)
            f.write("\n")
        written_files.append(str(path))
    return written_files
