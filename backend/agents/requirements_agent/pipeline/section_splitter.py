"""Lossless-first semantic section splitting for Requirements Agent.

The splitter keeps the original PRD text available through ``raw_text`` and
``raw_text_ref``. Processing text is normalized only for line endings and
non-semantic whitespace, then split by semantic headings before token chunking.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from backend.agents.requirements_agent.pipeline.token_limit_verify import (
    DEFAULT_HARD_TOKEN_LIMIT,
    DEFAULT_RECOMMENDED_TOKEN_LIMIT,
    estimate_tokens,
    verify_sections,
    verify_token_budget,
)

JsonObject = dict[str, Any]

DEFAULT_OVERLAP_TOKENS = 200
SECTION_KEYWORDS = (
    "overview",
    "background",
    "problem",
    "goal",
    "objective",
    "user scenario",
    "functional requirement",
    "feature",
    "non-functional",
    "technical constraint",
    "schedule",
    "budget",
    "risk",
    "acceptance criteria",
    "appendix",
    "개요",
    "배경",
    "문제",
    "목표",
    "사용자",
    "시나리오",
    "기능",
    "요구사항",
    "비기능",
    "기술",
    "제약",
    "일정",
    "예산",
    "리스크",
    "위험",
    "검수",
    "성공 기준",
)


@dataclass(frozen=True)
class TextSegment:
    """A lossless text unit with offsets relative to the parent section text."""

    text: str
    start: int
    end: int


def normalize_line_endings(raw_text: str) -> str:
    """Normalize line endings while preserving document content."""

    return raw_text.replace("\r\n", "\n").replace("\r", "\n")


def clean_document_text(raw_text: str) -> tuple[str, list[str]]:
    """Return processing text and cleaning notes without summarizing."""

    normalized = normalize_line_endings(raw_text)
    without_trailing_space = "\n".join(line.rstrip() for line in normalized.split("\n"))
    clean_text = re.sub(r"\n{4,}", "\n\n\n", without_trailing_space)
    notes = ["Normalized line endings for semantic section detection."]
    if clean_text != normalized:
        notes.append("Removed trailing spaces and collapsed excessive blank lines only.")
    return clean_text, notes


def prepare_document_sections(
    raw_text: str,
    *,
    document_id: str = "prd_document",
    document_type: str = "prd",
    source_uri: str | None = None,
    raw_text_ref: str | None = None,
    clean_text_ref: str | None = None,
    recommended_limit: int = DEFAULT_RECOMMENDED_TOKEN_LIMIT,
    hard_limit: int = DEFAULT_HARD_TOKEN_LIMIT,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> JsonObject:
    """Prepare preserved raw text, cleaned text, sections, and token checks."""

    clean_text, cleaning_notes = clean_document_text(raw_text)
    semantic_sections = split_semantic_sections(clean_text, document_id=document_id)
    processing_sections = chunk_sections(
        semantic_sections,
        hard_limit=hard_limit,
        target_tokens=recommended_limit,
        overlap_tokens=overlap_tokens,
    )
    raw_text_ref = raw_text_ref or f"memory://requirements_agent/{document_id}/raw_text"
    clean_text_ref = clean_text_ref or f"memory://requirements_agent/{document_id}/clean_text"
    section_token_checks = verify_sections(
        processing_sections,
        recommended_limit=recommended_limit,
        hard_limit=hard_limit,
    )
    return {
        "_meta": {
            "pipeline_phase": "token_limit_verify",
            "status": "completed" if raw_text.strip() else "empty_input",
            "created_at": datetime.now(UTC).isoformat(),
            "semantic_section_count": len(semantic_sections),
            "processing_section_count": len(processing_sections),
        },
        "document": {
            "document_id": document_id,
            "document_type": document_type,
            "source_uri": source_uri,
            "raw_text_ref": raw_text_ref,
            "clean_text_ref": clean_text_ref,
            "cleaning_notes": cleaning_notes,
        },
        "raw_text": raw_text,
        "clean_text": clean_text,
        "semantic_sections": semantic_sections,
        "sections": processing_sections,
        "document_token_check": verify_token_budget(
            clean_text,
            verify_id=f"token_verify_{document_id}_document",
            phase_name="document_preflight",
            target_phase="Token Limit Verify",
            recommended_limit=recommended_limit,
            hard_limit=hard_limit,
            included_context=["raw_prd_text"],
            excluded_context=["full_taxonomy", "full_rulebase", "raw_employee_db"],
            source_ref=raw_text_ref,
        ),
        "section_token_checks": section_token_checks,
        "chunking_policy": {
            "strategy": "semantic_sections_then_overlap_chunks",
            "target_tokens": recommended_limit,
            "hard_limit": hard_limit,
            "overlap_tokens": overlap_tokens,
            "lossless_first": True,
        },
        "preservation_policy": "raw_text_is_preserved_and_not_summarized",
    }


def split_semantic_sections(
    text: str,
    *,
    document_id: str = "prd_document",
) -> list[JsonObject]:
    """Split text into semantic sections using headings and paragraph fallback."""

    normalized = normalize_line_endings(text)
    lines = normalized.split("\n")
    heading_indices = [
        index
        for index, line in enumerate(lines)
        if _is_heading(
            line.strip(),
            index,
            previous_line=lines[index - 1].strip() if index > 0 else "",
            next_line=lines[index + 1].strip() if index + 1 < len(lines) else "",
        )
    ]
    if not heading_indices:
        return _paragraph_sections(normalized, document_id=document_id)

    sections: list[JsonObject] = []
    for number, start_line in enumerate(heading_indices, start=1):
        end_line = heading_indices[number] - 1 if number < len(heading_indices) else len(lines) - 1
        section_lines = lines[start_line : end_line + 1]
        joined_text = "\n".join(section_lines)
        section_text = joined_text.strip()
        if not section_text:
            continue
        start_char = _line_start_char(lines, start_line)
        leading_ws = len(joined_text) - len(joined_text.lstrip())
        start_char += leading_ws
        end_char = start_char + len(section_text)
        section_id = f"sec_{number:03d}"
        sections.append(
            _section_dict(
                section_id=section_id,
                section_title=_clean_heading(lines[start_line]) or f"Section {number}",
                section_text=section_text,
                source_range={
                    "page": None,
                    "start_char": start_char,
                    "end_char": end_char,
                    "start_line": start_line + 1,
                    "end_line": end_line + 1,
                },
                parent_section_id=None,
                chunk_id=None,
                overlap_with_previous=False,
            )
        )
    return sections


def chunk_sections(
    sections: Iterable[JsonObject],
    *,
    hard_limit: int = DEFAULT_HARD_TOKEN_LIMIT,
    target_tokens: int = DEFAULT_RECOMMENDED_TOKEN_LIMIT,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> list[JsonObject]:
    """Split over-limit sections into overlap chunks without summarizing."""

    chunked: list[JsonObject] = []
    for section in sections:
        if estimate_tokens(section["section_text"]) <= target_tokens:
            chunked.append(section)
            continue
        chunked.extend(
            _chunk_single_section(
                section,
                hard_limit=hard_limit,
                target_tokens=target_tokens,
                overlap_tokens=overlap_tokens,
            )
        )
    return chunked


def _chunk_single_section(
    section: JsonObject,
    *,
    hard_limit: int,
    target_tokens: int,
    overlap_tokens: int,
) -> list[JsonObject]:
    segments = _segments_for_chunking(section["section_text"], max_tokens=target_tokens)
    if not segments:
        return [section]

    body_token_limit = max(target_tokens - overlap_tokens, 1)
    grouped_segments: list[list[TextSegment]] = []
    current: list[TextSegment] = []
    for segment in segments:
        current_candidate = [*current, segment]
        if current and _segments_tokens(current_candidate) > body_token_limit:
            grouped_segments.append(current)
            current = [*_overlap_tail(current, overlap_tokens), segment]
            continue
        current = current_candidate
    if current:
        grouped_segments.append(current)

    section_chunks = [
        _chunk_dict(section, group, index, overlap_tokens=overlap_tokens)
        for index, group in enumerate(grouped_segments, start=1)
    ]
    return _enforce_hard_limit(
        section_chunks,
        hard_limit=hard_limit,
        overlap_tokens=overlap_tokens,
    )


def _enforce_hard_limit(
    chunks: list[JsonObject],
    *,
    hard_limit: int,
    overlap_tokens: int,
) -> list[JsonObject]:
    result: list[JsonObject] = []
    for chunk in chunks:
        if estimate_tokens(chunk["section_text"]) <= hard_limit:
            result.append(chunk)
            continue
        hard_segments = _char_window_segments(
            chunk["section_text"],
            max_tokens=max(hard_limit - overlap_tokens, 1),
            overlap_tokens=overlap_tokens,
        )
        for index, segment in enumerate(hard_segments, start=1):
            parent_section_id = chunk["parent_section_id"] or chunk["section_id"]
            chunk_id = f"{chunk['section_id']}_part_{index:03d}"
            source_start = int(chunk["source_range"].get("start_char") or 0) + segment.start
            source_end = int(chunk["source_range"].get("start_char") or 0) + segment.end
            result.append(
                _section_dict(
                    section_id=chunk_id,
                    section_title=f"{chunk['section_title']} / Part {index}",
                    section_text=segment.text,
                    source_range={
                        **chunk["source_range"],
                        "start_char": source_start,
                        "end_char": source_end,
                    },
                    parent_section_id=parent_section_id,
                    chunk_id=chunk_id,
                    overlap_with_previous=index > 1 or bool(chunk["overlap_with_previous"]),
                )
            )
    return result


def _paragraph_sections(text: str, *, document_id: str) -> list[JsonObject]:
    sections: list[JsonObject] = []
    for number, segment in enumerate(_paragraph_segments(text), start=1):
        start_line = text[: segment.start].count("\n") + 1
        end_line = text[: segment.end].count("\n") + 1
        sections.append(
            _section_dict(
                section_id=f"sec_{number:03d}",
                section_title=f"Section {number}" if segment.text else document_id,
                section_text=segment.text,
                source_range={
                    "page": None,
                    "start_char": segment.start,
                    "end_char": segment.end,
                    "start_line": start_line,
                    "end_line": end_line,
                },
                parent_section_id=None,
                chunk_id=None,
                overlap_with_previous=False,
            )
        )
    if not sections and text.strip():
        clean_text = text.strip()
        start_char = text.find(clean_text)
        sections.append(
            _section_dict(
                section_id="sec_001",
                section_title=document_id,
                section_text=clean_text,
                source_range={
                    "page": None,
                    "start_char": start_char,
                    "end_char": start_char + len(clean_text),
                    "start_line": 1,
                    "end_line": max(text.count("\n") + 1, 1),
                },
                parent_section_id=None,
                chunk_id=None,
                overlap_with_previous=False,
            )
        )
    return sections


def _section_dict(
    *,
    section_id: str,
    section_title: str,
    section_text: str,
    source_range: JsonObject,
    parent_section_id: str | None,
    chunk_id: str | None,
    overlap_with_previous: bool,
) -> JsonObject:
    return {
        "section_id": section_id,
        "section_title": section_title,
        "parent_section_id": parent_section_id,
        "chunk_id": chunk_id,
        "section_text": section_text,
        "source_range": source_range,
        "estimated_tokens": estimate_tokens(section_text),
        "overlap_with_previous": overlap_with_previous,
    }


def _chunk_dict(
    section: JsonObject,
    segments: list[TextSegment],
    chunk_number: int,
    *,
    overlap_tokens: int,
) -> JsonObject:
    section_text = "\n\n".join(segment.text for segment in segments).strip()
    chunk_id = f"{section['section_id']}_chunk_{chunk_number:03d}"
    base_start = int(section["source_range"].get("start_char") or 0)
    return _section_dict(
        section_id=chunk_id,
        section_title=f"{section['section_title']} / Chunk {chunk_number}",
        section_text=section_text,
        source_range={
            **section["source_range"],
            "start_char": base_start + min(segment.start for segment in segments),
            "end_char": base_start + max(segment.end for segment in segments),
        },
        parent_section_id=section["section_id"],
        chunk_id=chunk_id,
        overlap_with_previous=chunk_number > 1 and overlap_tokens > 0,
    )


def _is_heading(line: str, line_index: int, *, previous_line: str, next_line: str) -> bool:
    if not line:
        return False
    if re.match(r"^#{1,6}\s+\S+", line):
        return True
    if re.match(r"^\[[^\]]+\]$", line):
        return True
    cleaned = _clean_heading(line).casefold()
    if line_index == 0 and len(line) <= 100:
        return True
    has_heading_keyword = any(keyword in cleaned for keyword in SECTION_KEYWORDS)
    is_field_value_line = bool(re.match(r"^[^:：]{1,40}[:：]\s+\S+", line))
    if re.match(r"^\d+(\.\d+)*[.)]\s+\S+", line):
        return has_heading_keyword and not is_field_value_line
    return bool(
        len(line) <= 80
        and has_heading_keyword
        and not is_field_value_line
        and (not previous_line or not next_line)
    )


def _clean_heading(line: str) -> str:
    stripped = line.strip()
    stripped = re.sub(r"^#{1,6}\s+", "", stripped)
    stripped = re.sub(r"^\d+(\.\d+)*[.)]\s+", "", stripped)
    return stripped.strip("[] ")


def _line_start_char(lines: list[str], line_index: int) -> int:
    if line_index <= 0:
        return 0
    return sum(len(line) + 1 for line in lines[:line_index])


def _paragraph_segments(text: str) -> list[TextSegment]:
    return [
        TextSegment(match.group(0).strip(), match.start(), match.end())
        for match in re.finditer(r"\S.*?(?=\n\s*\n|\Z)", text, flags=re.DOTALL)
        if match.group(0).strip()
    ]


def _segments_for_chunking(text: str, *, max_tokens: int) -> list[TextSegment]:
    segments: list[TextSegment] = []
    for paragraph in _paragraph_segments(text):
        if estimate_tokens(paragraph.text) <= max_tokens:
            segments.append(paragraph)
            continue
        segments.extend(_sentence_segments(paragraph, max_tokens=max_tokens))
    return segments


def _sentence_segments(segment: TextSegment, *, max_tokens: int) -> list[TextSegment]:
    matches = list(re.finditer(r".+?(?:[.!?。！？](?=\s|$)|\n|$)", segment.text, flags=re.DOTALL))
    sentence_segments: list[TextSegment] = []
    for match in matches:
        text = match.group(0).strip()
        if not text:
            continue
        start = segment.start + match.start() + (len(match.group(0)) - len(match.group(0).lstrip()))
        end = start + len(text)
        sentence_segment = TextSegment(text, start, end)
        if estimate_tokens(sentence_segment.text) <= max_tokens:
            sentence_segments.append(sentence_segment)
            continue
        sentence_segments.extend(
            _char_window_segments(
                sentence_segment.text,
                max_tokens=max_tokens,
                overlap_tokens=0,
                base_start=sentence_segment.start,
            )
        )
    return sentence_segments


def _char_window_segments(
    text: str,
    *,
    max_tokens: int,
    overlap_tokens: int,
    base_start: int = 0,
) -> list[TextSegment]:
    max_chars = max(max_tokens * 4, 200)
    overlap_chars = max(overlap_tokens * 4, 0)
    segments: list[TextSegment] = []
    cursor = 0
    while cursor < len(text):
        end = min(cursor + max_chars, len(text))
        if end < len(text):
            boundary = max(text.rfind("\n", cursor, end), text.rfind(" ", cursor, end))
            if boundary > cursor:
                end = boundary
        segment_text = text[cursor:end].strip()
        if segment_text:
            leading_ws = len(text[cursor:end]) - len(text[cursor:end].lstrip())
            start = base_start + cursor + leading_ws
            segments.append(TextSegment(segment_text, start, start + len(segment_text)))
        if end >= len(text):
            break
        cursor = max(end - overlap_chars, cursor + 1)
    return segments


def _segments_tokens(segments: Iterable[TextSegment]) -> int:
    return estimate_tokens("\n\n".join(segment.text for segment in segments))


def _overlap_tail(segments: list[TextSegment], overlap_tokens: int) -> list[TextSegment]:
    if overlap_tokens <= 0:
        return []
    selected: list[TextSegment] = []
    for segment in reversed(segments):
        selected.insert(0, segment)
        if _segments_tokens(selected) >= overlap_tokens:
            break
    return selected
