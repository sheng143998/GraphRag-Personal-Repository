from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from uuid import uuid4

from app.core.pydantic_compat import model_copy_update
from app.schemas.ingest import ChunkRecord, DocumentIngestRequest, ParsedDocument


@dataclass(slots=True)
class TextSection:
    start: int
    end: int
    heading_path: list[str]
    section_index: int
    section_title: str | None


@dataclass(slots=True)
class TextUnit:
    start: int
    end: int
    split_level: str


@dataclass(slots=True)
class TextSegment:
    content: str
    char_start: int
    char_end: int
    split_level: str
    heading_path: list[str]
    section_index: int
    section_title: str | None


@dataclass(slots=True)
class TableData:
    header: list[str]
    rows: list[list[str]]
    header_row_number: int
    data_start_row_number: int
    sheet_name: str | None = None
    row_numbers: list[int] | None = None


@dataclass(slots=True)
class QAPair:
    question: str
    answer: str
    question_type: str


@dataclass(slots=True)
class CodeSegment:
    content: str
    char_start: int
    char_end: int
    language: str | None
    symbol_name: str | None
    symbol_type: str | None
    start_line: int
    end_line: int
    split_level: str


_HEADING_RE = re.compile(r"(?m)^(#{1,6})\s+(.+?)\s*$")
_ATOMIC_MARKDOWN_SPLIT_LEVELS = {"code-block", "image-reference"}
_FENCED_CODE_RE = re.compile(r"(?ms)^(```|~~~)[^\n]*\n.*?^\1\s*$")
_FENCED_CODE_WITH_INFO_RE = re.compile(r"(?ms)^(```|~~~)([^\n]*)\n(.*?)^\1\s*$")
_IMAGE_REFERENCE_LINE_RE = re.compile(
    r"(?m)^\s*(?:!\[[^\]]*]\([^)]+\)|!\[\[[^\]]+]]|\[\[[^\]]+\.(?:png|jpg|jpeg|gif|webp|svg)]])\s*$",
    re.I,
)
_CODE_SYMBOL_RE = re.compile(
    r"(?m)^(?P<indent>[ \t]*)"
    r"(?:(?P<pytype>def|class)\s+(?P<pyname>[A-Za-z_]\w*)\b"
    r"|(?:(?:export\s+)?(?:async\s+)?)function\s+(?P<jsfunc>[A-Za-z_]\w*)\s*\("
    r"|(?:export\s+)?class\s+(?P<jsclass>[A-Za-z_]\w*)\b"
    r"|(?:(?:public|private|protected|static|final|abstract|synchronized)\s+)+"
    r"[\w<>\[\], ?]+\s+(?P<javafunc>[A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{)",
)
_BOUNDARY_PATTERNS: tuple[tuple[str, str], ...] = (
    ("paragraph", r"\n\s*\n+"),
    ("line", r"\n+"),
    ("sentence", r"(?<=[.!?。！？])\s+|(?<=[。！？])"),
    ("punctuation", r"(?<=[,;，；])\s*"),
    ("word", r"\s+"),
)


class BaseChunker:
    async def chunk(
        self,
        *,
        parsed_document: ParsedDocument,
        request: DocumentIngestRequest,
    ) -> list[ChunkRecord]:
        raise NotImplementedError


class SimpleWindowChunker(BaseChunker):
    async def chunk(
        self,
        *,
        parsed_document: ParsedDocument,
        request: DocumentIngestRequest,
    ) -> list[ChunkRecord]:
        text = parsed_document.normalized_text
        if not text:
            return []

        size = _bounded_int(request.metadata.get("chunk_size"), default=500, minimum=100, maximum=2000)
        chunks: list[ChunkRecord] = []
        for index, offset in enumerate(range(0, len(text), size)):
            segment = _segment_from_range(
                source_text=text,
                start=offset,
                end=min(offset + size, len(text)),
                split_level="fixed-window",
                heading_path=[],
                section_index=index,
                section_title=None,
            )
            if segment is None:
                continue
            chunks.append(
                ChunkRecord(
                    chunk_id=str(uuid4()),
                    document_id=request.document_id,
                    knowledge_base_id=request.knowledge_base_id,
                    title=parsed_document.title,
                    chunk_index=len(chunks),
                    content=segment.content,
                    metadata=_chunk_metadata(
                        parsed_document=parsed_document,
                        request=request,
                        content=segment.content,
                        chunk_strategy="simple-window",
                        chunk_level="child",
                        extra={
                            "chunk_algorithm": "fixed-character-window",
                            "chunk_size": size,
                            "chunk_overlap": 0,
                            "char_start": segment.char_start,
                            "char_end": segment.char_end,
                            "split_level": segment.split_level,
                            "heading_path": segment.heading_path,
                            "section_index": segment.section_index,
                        },
                    ),
                )
            )
        return chunks


class SimpleChunker(BaseChunker):
    async def chunk(
        self,
        *,
        parsed_document: ParsedDocument,
        request: DocumentIngestRequest,
    ) -> list[ChunkRecord]:
        text = parsed_document.normalized_text
        if not text:
            return []

        chunk_size = _bounded_int(request.metadata.get("chunk_size"), default=800, minimum=200, maximum=2500)
        chunk_overlap = _bounded_int(request.metadata.get("chunk_overlap"), default=120, minimum=0, maximum=600)
        chunk_overlap = min(chunk_overlap, max(0, chunk_size // 2))
        min_chunk_size = _bounded_int(
            request.metadata.get("min_chunk_size"),
            default=120,
            minimum=40,
            maximum=max(40, chunk_size),
        )

        segments = _recursive_document_segments(
            source_text=text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            min_chunk_size=min_chunk_size,
        )
        chunks: list[ChunkRecord] = []
        for segment in segments:
            chunks.append(
                ChunkRecord(
                    chunk_id=str(uuid4()),
                    document_id=request.document_id,
                    knowledge_base_id=request.knowledge_base_id,
                    title=_chunk_title(parsed_document.title, segment.section_title),
                    chunk_index=len(chunks),
                    content=segment.content,
                    metadata=_chunk_metadata(
                        parsed_document=parsed_document,
                        request=request,
                        content=segment.content,
                        chunk_strategy="recursive-overlap",
                        chunk_level="child",
                        extra={
                            "chunk_algorithm": "recursive-overlap",
                            "chunk_size": chunk_size,
                            "chunk_overlap": chunk_overlap,
                            "min_chunk_size": min_chunk_size,
                            "char_start": segment.char_start,
                            "char_end": segment.char_end,
                            "split_level": segment.split_level,
                            "heading_path": segment.heading_path,
                            "section_index": segment.section_index,
                            "section_title": segment.section_title,
                        },
                    ),
                )
            )
        return chunks


class TableRowGroupChunker(BaseChunker):
    async def chunk(
        self,
        *,
        parsed_document: ParsedDocument,
        request: DocumentIngestRequest,
    ) -> list[ChunkRecord]:
        text = parsed_document.normalized_text
        if not text:
            return []

        tables = _spreadsheet_tables_from_metadata(parsed_document.metadata)
        if not tables:
            table = _parse_table_text(text)
            if table is not None:
                table.sheet_name = _table_sheet_name(parsed_document=parsed_document, request=request)
            tables = [table] if table is not None else []
        tables = [table for table in tables if table is not None and table.rows]
        if not tables:
            return await SimpleChunker().chunk(parsed_document=parsed_document, request=request)

        row_group_size = _bounded_int(
            request.metadata.get("table_row_group_size"),
            default=25,
            minimum=1,
            maximum=100,
        )
        chunks: list[ChunkRecord] = []
        for table_index, table in enumerate(tables):
            sheet_name = table.sheet_name or _table_sheet_name(parsed_document=parsed_document, request=request)
            for group_index, offset in enumerate(range(0, len(table.rows), row_group_size)):
                row_group = table.rows[offset : offset + row_group_size]
                row_numbers = table.row_numbers[offset : offset + len(row_group)] if table.row_numbers else None
                row_start = row_numbers[0] if row_numbers else table.data_start_row_number + offset
                row_end = row_numbers[-1] if row_numbers else row_start + len(row_group) - 1
                content = _table_group_content(
                    sheet_name=sheet_name,
                    columns=table.header,
                    rows=row_group,
                    row_start=row_start,
                    row_numbers=row_numbers,
                )
                chunks.append(
                    ChunkRecord(
                        chunk_id=str(uuid4()),
                        document_id=request.document_id,
                        knowledge_base_id=request.knowledge_base_id,
                        title=f"{parsed_document.title} / {sheet_name} rows {row_start}-{row_end}",
                        chunk_index=len(chunks),
                        content=content,
                        metadata=_chunk_metadata(
                            parsed_document=parsed_document,
                            request=request,
                            content=content,
                            chunk_strategy="table-row-group",
                            chunk_level="child",
                            extra={
                                "chunk_algorithm": "table-row-group",
                                "chunk_size": row_group_size,
                                "chunk_overlap": 0,
                                "split_level": "table-row-group",
                                "block_type": "table_rows",
                                "sheet_name": sheet_name,
                                "row_range": f"{row_start}-{row_end}",
                                "row_start": row_start,
                                "row_end": row_end,
                                "row_count": len(row_group),
                                "row_group_index": group_index,
                                "header_row": table.header_row_number,
                                "column_names": table.header,
                                "table_index": table_index,
                            },
                        ),
                    )
                )
        return chunks


class QAPairChunker(BaseChunker):
    async def chunk(
        self,
        *,
        parsed_document: ParsedDocument,
        request: DocumentIngestRequest,
    ) -> list[ChunkRecord]:
        text = parsed_document.normalized_text
        if not text:
            return []

        pairs = _parse_qa_pairs(text)
        if not pairs:
            return await SimpleChunker().chunk(parsed_document=parsed_document, request=request)

        chunks: list[ChunkRecord] = []
        for index, pair in enumerate(pairs):
            content = _qa_pair_content(pair)
            chunks.append(
                ChunkRecord(
                    chunk_id=str(uuid4()),
                    document_id=request.document_id,
                    knowledge_base_id=request.knowledge_base_id,
                    title=_qa_pair_title(parsed_document.title, pair, index),
                    chunk_index=len(chunks),
                    content=content,
                    metadata=_chunk_metadata(
                        parsed_document=parsed_document,
                        request=request,
                        content=content,
                        chunk_strategy="qna-pair",
                        chunk_level="child",
                        extra={
                            "chunk_algorithm": "qna-pair",
                            "chunk_size": len(content),
                            "chunk_overlap": 0,
                            "split_level": "qa-pair",
                            "block_type": "qa_pair",
                            "question_text": pair.question,
                            "answer_text": pair.answer,
                            "qa_pair_index": index,
                            "qa_question_type": pair.question_type,
                        },
                    ),
                )
            )
        return chunks


class CodeAwareChunker(BaseChunker):
    async def chunk(
        self,
        *,
        parsed_document: ParsedDocument,
        request: DocumentIngestRequest,
    ) -> list[ChunkRecord]:
        text = parsed_document.normalized_text
        if not text:
            return []

        segments = _code_segments(
            text,
            default_language=_code_language(parsed_document=parsed_document, request=request),
        )
        if not segments:
            return await SimpleChunker().chunk(parsed_document=parsed_document, request=request)

        chunks: list[ChunkRecord] = []
        for index, segment in enumerate(segments):
            chunks.append(
                ChunkRecord(
                    chunk_id=str(uuid4()),
                    document_id=request.document_id,
                    knowledge_base_id=request.knowledge_base_id,
                    title=_code_chunk_title(parsed_document.title, segment, index),
                    chunk_index=len(chunks),
                    content=segment.content,
                    metadata=_chunk_metadata(
                        parsed_document=parsed_document,
                        request=request,
                        content=segment.content,
                        chunk_strategy="code-aware",
                        chunk_level="child",
                        extra={
                            "chunk_algorithm": "code-aware",
                            "chunk_size": len(segment.content),
                            "chunk_overlap": 0,
                            "split_level": segment.split_level,
                            "block_type": "code",
                            "language": segment.language,
                            "symbol_name": segment.symbol_name,
                            "symbol_type": segment.symbol_type,
                            "code_segment_index": index,
                            "char_start": segment.char_start,
                            "char_end": segment.char_end,
                            "start_line": segment.start_line,
                            "end_line": segment.end_line,
                        },
                    ),
                )
            )
        return chunks


class ParentChildChunker(BaseChunker):
    async def chunk(
        self,
        *,
        parsed_document: ParsedDocument,
        request: DocumentIngestRequest,
    ) -> list[ChunkRecord]:
        text = parsed_document.normalized_text
        if not text:
            return []

        parent_size = _bounded_int(request.metadata.get("parent_chunk_size"), default=1500, minimum=500, maximum=5000)
        parent_overlap = _bounded_int(request.metadata.get("parent_chunk_overlap"), default=0, minimum=0, maximum=800)
        parent_overlap = min(parent_overlap, max(0, parent_size // 3))
        child_size = _bounded_int(request.metadata.get("child_chunk_size"), default=500, minimum=100, maximum=1500)
        child_overlap = _bounded_int(request.metadata.get("child_chunk_overlap"), default=80, minimum=0, maximum=500)
        child_overlap = min(child_overlap, max(0, child_size // 2))
        min_child_size = _bounded_int(
            request.metadata.get("min_child_chunk_size"),
            default=80,
            minimum=30,
            maximum=max(30, child_size),
        )
        if child_size >= parent_size:
            child_size = max(100, parent_size // 3)
            child_overlap = min(child_overlap, max(0, child_size // 2))

        parent_segments = _parent_segments(
            source_text=text,
            parent_size=parent_size,
            parent_overlap=parent_overlap,
        )
        chunks: list[ChunkRecord] = []
        chunk_index = 0
        for parent_ordinal, parent_segment in enumerate(parent_segments):
            parent_id = str(uuid4())
            child_segments = _recursive_segments_for_range(
                source_text=text,
                start=parent_segment.char_start,
                end=parent_segment.char_end,
                chunk_size=child_size,
                chunk_overlap=child_overlap,
                min_chunk_size=min_child_size,
                heading_path=parent_segment.heading_path,
                section_index=parent_segment.section_index,
                section_title=parent_segment.section_title,
            )
            if _child_segments_duplicate_parent(parent_segment, child_segments):
                chunks.append(
                    ChunkRecord(
                        chunk_id=str(uuid4()),
                        document_id=request.document_id,
                        knowledge_base_id=request.knowledge_base_id,
                        title=_chunk_title(parsed_document.title, parent_segment.section_title),
                        chunk_index=chunk_index,
                        content=parent_segment.content,
                        metadata=_chunk_metadata(
                            parsed_document=parsed_document,
                            request=request,
                            content=parent_segment.content,
                            chunk_strategy="recursive-overlap",
                            chunk_level="child",
                            extra={
                                "chunk_algorithm": "parent-child-single-child-downgrade",
                                "chunk_size": child_size,
                                "chunk_overlap": child_overlap,
                                "min_chunk_size": min_child_size,
                                "char_start": parent_segment.char_start,
                                "char_end": parent_segment.char_end,
                                "split_level": parent_segment.split_level,
                                "heading_path": parent_segment.heading_path,
                                "section_index": parent_segment.section_index,
                                "section_title": parent_segment.section_title,
                                "parent_child_downgrade_reason": "single-child-identical-parent",
                            },
                        ),
                    )
                )
                chunk_index += 1
                continue
            child_records: list[ChunkRecord] = []
            for child_ordinal, child_segment in enumerate(child_segments):
                child_records.append(
                    ChunkRecord(
                        chunk_id=str(uuid4()),
                        document_id=request.document_id,
                        knowledge_base_id=request.knowledge_base_id,
                        parent_chunk_id=parent_id,
                        title=_chunk_title(parsed_document.title, child_segment.section_title),
                        chunk_index=0,
                        content=child_segment.content,
                        metadata=_chunk_metadata(
                            parsed_document=parsed_document,
                            request=request,
                            content=child_segment.content,
                            chunk_strategy="parent-child",
                            chunk_level="child",
                            extra={
                                "chunk_algorithm": "section-parent-recursive-child",
                                "chunk_size": child_size,
                                "chunk_overlap": child_overlap,
                                "min_chunk_size": min_child_size,
                                "char_start": child_segment.char_start,
                                "char_end": child_segment.char_end,
                                "split_level": child_segment.split_level,
                                "heading_path": child_segment.heading_path,
                                "section_index": child_segment.section_index,
                                "section_title": child_segment.section_title,
                                "parent_heading": parent_segment.section_title,
                                "parent_char_start": parent_segment.char_start,
                                "parent_char_end": parent_segment.char_end,
                                "child_index_in_parent": child_ordinal,
                            },
                        ),
                    )
                )

            chunks.append(
                ChunkRecord(
                    chunk_id=parent_id,
                    document_id=request.document_id,
                    knowledge_base_id=request.knowledge_base_id,
                    title=_chunk_title(parsed_document.title, parent_segment.section_title),
                    chunk_index=chunk_index,
                    content=parent_segment.content,
                    metadata=_chunk_metadata(
                        parsed_document=parsed_document,
                        request=request,
                        content=parent_segment.content,
                        chunk_strategy="parent-child",
                        chunk_level="parent",
                        extra={
                            "chunk_algorithm": "section-parent-recursive-child",
                            "chunk_size": parent_size,
                            "chunk_overlap": parent_overlap,
                            "char_start": parent_segment.char_start,
                            "char_end": parent_segment.char_end,
                            "split_level": parent_segment.split_level,
                            "heading_path": parent_segment.heading_path,
                            "section_index": parent_segment.section_index,
                            "section_title": parent_segment.section_title,
                            "parent_index": parent_ordinal,
                            "child_chunk_size": child_size,
                            "child_chunk_overlap": child_overlap,
                            "child_count": len(child_records),
                            "child_chunk_ids": [child.chunk_id for child in child_records],
                        },
                    ),
                )
            )
            chunk_index += 1

            for child in child_records:
                chunks.append(model_copy_update(child, {"chunk_index": chunk_index}))
                chunk_index += 1
        return chunks


def _recursive_document_segments(
    *,
    source_text: str,
    chunk_size: int,
    chunk_overlap: int,
    min_chunk_size: int,
) -> list[TextSegment]:
    segments: list[TextSegment] = []
    for section in _document_sections(source_text):
        segments.extend(
            _recursive_segments_for_range(
                source_text=source_text,
                start=section.start,
                end=section.end,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                min_chunk_size=min_chunk_size,
                heading_path=section.heading_path,
                section_index=section.section_index,
                section_title=section.section_title,
            )
        )
    return segments


def _child_segments_duplicate_parent(parent_segment: TextSegment, child_segments: list[TextSegment]) -> bool:
    if len(child_segments) != 1:
        return False
    return child_segments[0].content.strip() == parent_segment.content.strip()


def _parent_segments(*, source_text: str, parent_size: int, parent_overlap: int) -> list[TextSegment]:
    parent_segments: list[TextSegment] = []
    for section in _document_sections(source_text):
        section_segment = _segment_from_range(
            source_text=source_text,
            start=section.start,
            end=section.end,
            split_level="section",
            heading_path=section.heading_path,
            section_index=section.section_index,
            section_title=section.section_title,
        )
        if section_segment is None:
            continue
        if len(section_segment.content) <= parent_size:
            parent_segments.append(section_segment)
            continue
        parent_segments.extend(
            _recursive_segments_for_range(
                source_text=source_text,
                start=section_segment.char_start,
                end=section_segment.char_end,
                chunk_size=parent_size,
                chunk_overlap=parent_overlap,
                min_chunk_size=min(200, parent_size),
                heading_path=section.heading_path,
                section_index=section.section_index,
                section_title=section.section_title,
            )
        )
    return _deduplicate_segments(parent_segments)


def _recursive_segments_for_range(
    *,
    source_text: str,
    start: int,
    end: int,
    chunk_size: int,
    chunk_overlap: int,
    min_chunk_size: int,
    heading_path: list[str],
    section_index: int,
    section_title: str | None,
) -> list[TextSegment]:
    raw_text = source_text[start:end]
    units = _split_units_recursive(raw_text, start, chunk_size)
    if not units:
        return []
    segments = _pack_units(
        source_text=source_text,
        units=units,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        heading_path=heading_path,
        section_index=section_index,
        section_title=section_title,
    )
    return _deduplicate_segments(
        _merge_short_segments(
            source_text=source_text,
            segments=segments,
            min_chunk_size=min_chunk_size,
            max_chunk_size=chunk_size,
        )
    )


def _deduplicate_segments(segments: list[TextSegment]) -> list[TextSegment]:
    deduped: list[TextSegment] = []
    seen: set[tuple[tuple[str, ...], str | None, str]] = set()
    for segment in segments:
        key = (tuple(segment.heading_path), segment.section_title, _normalize_duplicate_text(segment.content))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(segment)
    return deduped


def _normalize_duplicate_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _document_sections(text: str) -> list[TextSection]:
    matches = list(_HEADING_RE.finditer(text))
    if not matches:
        return [TextSection(start=0, end=len(text), heading_path=[], section_index=0, section_title=None)]

    sections: list[TextSection] = []
    section_index = 0
    if matches[0].start() > 0 and text[: matches[0].start()].strip():
        sections.append(
            TextSection(
                start=0,
                end=matches[0].start(),
                heading_path=[],
                section_index=section_index,
                section_title=None,
            )
        )
        section_index += 1

    heading_stack: list[tuple[int, str]] = []
    for match_index, match in enumerate(matches):
        level = len(match.group(1))
        title = _clean_heading(match.group(2))
        heading_stack = [item for item in heading_stack if item[0] < level]
        heading_stack.append((level, title))
        end = matches[match_index + 1].start() if match_index + 1 < len(matches) else len(text)
        if not text[match.start() : end].strip():
            continue
        sections.append(
            TextSection(
                start=match.start(),
                end=end,
                heading_path=[item[1] for item in heading_stack],
                section_index=section_index,
                section_title=title,
            )
        )
        section_index += 1

    return sections or [TextSection(start=0, end=len(text), heading_path=[], section_index=0, section_title=None)]


def _split_units_recursive(
    text: str,
    base_start: int,
    max_size: int,
    boundary_index: int = 0,
    split_level: str = "section",
) -> list[TextUnit]:
    trimmed = _trim_text_range(text, base_start, base_start + len(text))
    if trimmed is None:
        return []
    char_start, char_end, content = trimmed
    atomic_units = _markdown_atomic_units(content, char_start, max_size, boundary_index, split_level)
    if atomic_units is not None:
        return atomic_units
    if len(content) <= max_size:
        return [TextUnit(start=char_start, end=char_end, split_level=split_level)]

    if boundary_index >= len(_BOUNDARY_PATTERNS):
        return _window_units(content, char_start, max_size)

    next_level, pattern = _BOUNDARY_PATTERNS[boundary_index]
    pieces = _split_by_boundary(content, char_start, pattern)
    if len(pieces) <= 1:
        return _split_units_recursive(
            content,
            char_start,
            max_size,
            boundary_index + 1,
            split_level,
        )

    units: list[TextUnit] = []
    for piece_start, piece_end in pieces:
        units.extend(
            _split_units_recursive(
                text[piece_start - base_start : piece_end - base_start],
                piece_start,
                max_size,
                boundary_index + 1,
                next_level,
            )
        )
    return units


def _markdown_atomic_units(
    text: str,
    base_start: int,
    max_size: int,
    boundary_index: int,
    split_level: str,
) -> list[TextUnit] | None:
    spans = _markdown_atomic_spans(text)
    if not spans:
        return None

    units: list[TextUnit] = []
    cursor = 0
    for start, end, atomic_level in spans:
        if start > cursor:
            units.extend(
                _split_units_recursive(
                    text[cursor:start],
                    base_start + cursor,
                    max_size,
                    boundary_index,
                    split_level,
                )
            )
        trimmed = _trim_text_range(text[start:end], base_start + start, base_start + end)
        if trimmed is not None:
            units.append(TextUnit(start=trimmed[0], end=trimmed[1], split_level=atomic_level))
        cursor = end

    if cursor < len(text):
        units.extend(
            _split_units_recursive(
                text[cursor:],
                base_start + cursor,
                max_size,
                boundary_index,
                split_level,
            )
        )
    return units


def _markdown_atomic_spans(text: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    for match in _FENCED_CODE_RE.finditer(text):
        spans.append((match.start(), match.end(), "code-block"))
    for match in _IMAGE_REFERENCE_LINE_RE.finditer(text):
        spans.append((match.start(), match.end(), "image-reference"))
    if not spans:
        return []

    merged: list[tuple[int, int, str]] = []
    for start, end, level in sorted(spans, key=lambda item: (item[0], item[1])):
        if merged and start < merged[-1][1]:
            continue
        merged.append((start, end, level))
    return merged


def _split_by_boundary(text: str, base_start: int, pattern: str) -> list[tuple[int, int]]:
    pieces: list[tuple[int, int]] = []
    last = 0
    for match in re.finditer(pattern, text):
        boundary = match.end()
        if boundary <= last:
            continue
        trimmed = _trim_text_range(text[last:boundary], base_start + last, base_start + boundary)
        if trimmed is not None:
            pieces.append((trimmed[0], trimmed[1]))
        last = boundary
    if last < len(text):
        trimmed = _trim_text_range(text[last:], base_start + last, base_start + len(text))
        if trimmed is not None:
            pieces.append((trimmed[0], trimmed[1]))
    return pieces


def _window_units(text: str, base_start: int, max_size: int) -> list[TextUnit]:
    units: list[TextUnit] = []
    for offset in range(0, len(text), max_size):
        trimmed = _trim_text_range(text[offset : offset + max_size], base_start + offset, base_start + offset + max_size)
        if trimmed is not None:
            units.append(TextUnit(start=trimmed[0], end=trimmed[1], split_level="window"))
    return units


def _pack_units(
    *,
    source_text: str,
    units: list[TextUnit],
    chunk_size: int,
    chunk_overlap: int,
    heading_path: list[str],
    section_index: int,
    section_title: str | None,
) -> list[TextSegment]:
    segments: list[TextSegment] = []
    current: list[TextUnit] = []
    for unit in units:
        if unit.split_level in _ATOMIC_MARKDOWN_SPLIT_LEVELS:
            if current:
                segment = _segment_from_units(source_text, current, heading_path, section_index, section_title)
                if segment is not None:
                    segments.append(segment)
                current = []
            segment = _segment_from_units(source_text, [unit], heading_path, section_index, section_title)
            if segment is not None:
                segments.append(segment)
            continue
        if current and unit.end - current[0].start > chunk_size:
            segment = _segment_from_units(source_text, current, heading_path, section_index, section_title)
            if segment is not None:
                segments.append(segment)
            current = _tail_overlap_units(current, chunk_overlap)
            if current and unit.end - current[0].start > chunk_size:
                current = []
        current.append(unit)

    if current:
        segment = _segment_from_units(source_text, current, heading_path, section_index, section_title)
        if segment is not None:
            segments.append(segment)
    return segments


def _tail_overlap_units(units: list[TextUnit], chunk_overlap: int) -> list[TextUnit]:
    if chunk_overlap <= 0:
        return []
    tail: list[TextUnit] = []
    for unit in reversed(units):
        tail.insert(0, unit)
        if tail[-1].end - tail[0].start >= chunk_overlap:
            break
    return tail


def _segment_from_units(
    source_text: str,
    units: list[TextUnit],
    heading_path: list[str],
    section_index: int,
    section_title: str | None,
) -> TextSegment | None:
    if not units:
        return None
    return _segment_from_range(
        source_text=source_text,
        start=units[0].start,
        end=units[-1].end,
        split_level=_dominant_split_level(units),
        heading_path=heading_path,
        section_index=section_index,
        section_title=section_title,
    )


def _segment_from_range(
    *,
    source_text: str,
    start: int,
    end: int,
    split_level: str,
    heading_path: list[str],
    section_index: int,
    section_title: str | None,
) -> TextSegment | None:
    trimmed = _trim_text_range(source_text[start:end], start, end)
    if trimmed is None:
        return None
    char_start, char_end, content = trimmed
    return TextSegment(
        content=content,
        char_start=char_start,
        char_end=char_end,
        split_level=split_level,
        heading_path=heading_path,
        section_index=section_index,
        section_title=section_title,
    )


def _merge_short_segments(
    *,
    source_text: str,
    segments: list[TextSegment],
    min_chunk_size: int,
    max_chunk_size: int,
) -> list[TextSegment]:
    if len(segments) <= 1:
        return segments
    merged: list[TextSegment] = []
    for segment in segments:
        if (
            merged
            and segment.split_level not in _ATOMIC_MARKDOWN_SPLIT_LEVELS
            and merged[-1].split_level not in _ATOMIC_MARKDOWN_SPLIT_LEVELS
            and len(segment.content) < min_chunk_size
            and segment.section_index == merged[-1].section_index
            and segment.char_end - merged[-1].char_start <= max_chunk_size + min_chunk_size
        ):
            previous = merged.pop()
            combined = _segment_from_range(
                source_text=source_text,
                start=previous.char_start,
                end=segment.char_end,
                split_level=previous.split_level if previous.split_level == segment.split_level else "mixed",
                heading_path=previous.heading_path,
                section_index=previous.section_index,
                section_title=previous.section_title,
            )
            if combined is not None:
                merged.append(combined)
            continue
        merged.append(segment)
    return merged


def _parse_table_text(text: str) -> TableData | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None
    if _looks_like_markdown_pipe_table(lines):
        return _parse_pipe_table(lines)
    return _parse_delimited_table(text)


def _looks_like_markdown_pipe_table(lines: list[str]) -> bool:
    pipe_lines = sum(1 for line in lines[:10] if line.count("|") >= 2)
    return pipe_lines >= 2


def _parse_pipe_table(lines: list[str]) -> TableData | None:
    rows: list[list[str]] = []
    for line in lines:
        if re.fullmatch(r"\|?[-:| ]{3,}\|?", line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if any(cells):
            rows.append(cells)
    return _table_from_rows(rows)


def _parse_delimited_table(text: str) -> TableData | None:
    sample = "\n".join(text.splitlines()[:20])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t;")
    except csv.Error:
        dialect = csv.excel
    rows = [
        [cell.strip() for cell in row]
        for row in csv.reader(text.splitlines(), dialect)
        if any(str(cell).strip() for cell in row)
    ]
    return _table_from_rows(rows)


def _table_from_rows(rows: list[list[str]]) -> TableData | None:
    if not rows:
        return None
    width = max(len(row) for row in rows)
    normalized_rows = [_pad_row(row, width) for row in rows]
    header = [_clean_column_name(value, index) for index, value in enumerate(normalized_rows[0])]
    data_rows = normalized_rows[1:] if len(normalized_rows) > 1 else normalized_rows
    if len(normalized_rows) == 1:
        header = [f"column_{index + 1}" for index in range(width)]
    data_rows = [row for row in data_rows if any(cell.strip() for cell in row)]
    if not data_rows:
        return None
    return TableData(
        header=header,
        rows=data_rows,
        header_row_number=1 if len(normalized_rows) > 1 else 0,
        data_start_row_number=2 if len(normalized_rows) > 1 else 1,
    )


def _pad_row(row: list[str], width: int) -> list[str]:
    return [str(value).strip() for value in row] + [""] * max(0, width - len(row))


def _clean_column_name(value: str, index: int) -> str:
    text = str(value).strip()
    return text or f"column_{index + 1}"


def _table_sheet_name(*, parsed_document: ParsedDocument, request: DocumentIngestRequest) -> str:
    explicit = request.metadata.get("sheet_name") or request.metadata.get("sheetName")
    if explicit:
        return str(explicit).strip() or "Sheet1"
    parsed_sheet = parsed_document.metadata.get("sheet_name") or parsed_document.metadata.get("sheetName")
    if parsed_sheet:
        return str(parsed_sheet).strip() or "Sheet1"
    return "Sheet1"


def _spreadsheet_tables_from_metadata(metadata: dict[str, object]) -> list[TableData]:
    raw_tables = metadata.get("spreadsheet_tables")
    if not isinstance(raw_tables, list):
        return []
    tables: list[TableData] = []
    for raw_table in raw_tables:
        if not isinstance(raw_table, dict):
            continue
        header = [str(value).strip() for value in raw_table.get("header", []) if str(value).strip()]
        raw_rows = raw_table.get("rows", [])
        if not header or not isinstance(raw_rows, list):
            continue
        rows = [
            [str(value).strip() for value in row]
            for row in raw_rows
            if isinstance(row, list) and any(str(value).strip() for value in row)
        ]
        if not rows:
            continue
        row_numbers = [
            int(value)
            for value in raw_table.get("row_numbers", [])
            if isinstance(value, int) or (isinstance(value, str) and value.isdigit())
        ]
        if len(row_numbers) != len(rows):
            row_numbers = []
        tables.append(
            TableData(
                header=header,
                rows=rows,
                header_row_number=_metadata_int(raw_table.get("header_row_number"), 1),
                data_start_row_number=_metadata_int(raw_table.get("data_start_row_number"), 2),
                sheet_name=str(raw_table.get("sheet_name") or "Sheet1").strip() or "Sheet1",
                row_numbers=row_numbers or None,
            )
        )
    return tables


def _metadata_int(value: object, default: int) -> int:
    try:
        return int(str(value))
    except Exception:
        return default


def _table_group_content(
    *,
    sheet_name: str,
    columns: list[str],
    rows: list[list[str]],
    row_start: int,
    row_numbers: list[int] | None = None,
) -> str:
    lines = [
        f"Sheet: {sheet_name}",
        "Columns: " + " | ".join(columns),
    ]
    for index, row in enumerate(rows):
        row_number = row_numbers[index] if row_numbers and index < len(row_numbers) else row_start + index
        values = [
            f"{column}={value}"
            for column, value in zip(columns, row, strict=False)
            if str(value).strip()
        ]
        lines.append(f"Row {row_number}: " + " | ".join(values))
    return "\n".join(lines)


def _code_segments(text: str, default_language: str | None) -> list[CodeSegment]:
    fenced_segments = _fenced_code_segments(text, default_language)
    if fenced_segments:
        return fenced_segments

    symbol_segments = _symbol_code_segments(text, default_language)
    if symbol_segments:
        return symbol_segments

    if _looks_like_code_text(text):
        stripped = text.strip()
        char_start = text.find(stripped)
        char_end = char_start + len(stripped)
        return [
            CodeSegment(
                content=stripped,
                char_start=char_start,
                char_end=char_end,
                language=default_language,
                symbol_name=None,
                symbol_type=None,
                start_line=_line_number_at(text, char_start),
                end_line=_line_number_at(text, char_end),
                split_level="code-document",
            )
        ]
    return []


def _fenced_code_segments(text: str, default_language: str | None) -> list[CodeSegment]:
    segments: list[CodeSegment] = []
    for match in _FENCED_CODE_WITH_INFO_RE.finditer(text):
        content = match.group(0).strip()
        info = match.group(2).strip()
        language = info.split()[0].lower() if info else default_language
        symbol_type, symbol_name = _first_code_symbol(match.group(3))
        segments.append(
            CodeSegment(
                content=content,
                char_start=match.start(),
                char_end=match.end(),
                language=language,
                symbol_name=symbol_name,
                symbol_type=symbol_type,
                start_line=_line_number_at(text, match.start()),
                end_line=_line_number_at(text, match.end()),
                split_level="code-block",
            )
        )
    return segments


def _symbol_code_segments(text: str, default_language: str | None) -> list[CodeSegment]:
    matches = list(_CODE_SYMBOL_RE.finditer(text))
    if not matches:
        return []
    min_indent = min(len(match.group("indent") or "") for match in matches)
    matches = [match for match in matches if len(match.group("indent") or "") == min_indent]

    segments: list[CodeSegment] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        trimmed = _trim_text_range(text[start:end], start, end)
        if trimmed is None:
            continue
        char_start, char_end, content = trimmed
        symbol_type, symbol_name = _code_symbol_from_match(match)
        segments.append(
            CodeSegment(
                content=content,
                char_start=char_start,
                char_end=char_end,
                language=default_language,
                symbol_name=symbol_name,
                symbol_type=symbol_type,
                start_line=_line_number_at(text, char_start),
                end_line=_line_number_at(text, char_end),
                split_level="code-symbol",
            )
        )
    return segments


def _first_code_symbol(code: str) -> tuple[str | None, str | None]:
    match = _CODE_SYMBOL_RE.search(code)
    return _code_symbol_from_match(match) if match else (None, None)


def _code_symbol_from_match(match: re.Match[str]) -> tuple[str | None, str | None]:
    pytype = match.groupdict().get("pytype")
    pyname = match.groupdict().get("pyname")
    if pytype and pyname:
        return ("class" if pytype == "class" else "function"), pyname
    if match.groupdict().get("jsclass"):
        return "class", match.group("jsclass")
    if match.groupdict().get("jsfunc"):
        return "function", match.group("jsfunc")
    if match.groupdict().get("javafunc"):
        return "method", match.group("javafunc")
    return None, None


def _code_language(*, parsed_document: ParsedDocument, request: DocumentIngestRequest) -> str | None:
    explicit = request.metadata.get("language") or request.metadata.get("code_language")
    if explicit:
        return str(explicit).strip().lower() or None
    parsed = parsed_document.metadata.get("language") or parsed_document.metadata.get("code_language")
    if parsed:
        return str(parsed).strip().lower() or None
    filename = str(request.file.filename).lower()
    extension = filename.rsplit(".", 1)[-1] if "." in filename else ""
    return {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "java": "java",
        "go": "go",
        "sql": "sql",
        "sh": "shell",
        "ps1": "powershell",
    }.get(extension)


def _code_chunk_title(document_title: str, segment: CodeSegment, index: int) -> str:
    if segment.symbol_name:
        return f"{document_title} / {segment.symbol_name}"
    if segment.language:
        return f"{document_title} / {segment.language} code {index + 1}"
    return f"{document_title} / code {index + 1}"


def _line_number_at(text: str, offset: int) -> int:
    return text.count("\n", 0, max(0, min(offset, len(text)))) + 1


def _looks_like_code_text(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    code_markers = (
        "import ",
        "from ",
        "package ",
        "public ",
        "private ",
        "protected ",
        "const ",
        "let ",
        "var ",
        "SELECT ",
        "CREATE ",
        "#!/bin/",
    )
    upper = stripped.upper()
    return (
        any(stripped.startswith(marker) for marker in code_markers)
        or any(upper.startswith(marker) for marker in ("SELECT ", "CREATE ", "WITH "))
        or stripped.count("{") + stripped.count("}") >= 2
        or stripped.count(";") >= 2
    )


def _parse_qa_pairs(text: str) -> list[QAPair]:
    pairs: list[QAPair] = []
    current_question: str | None = None
    answer_lines: list[str] = []
    in_answer = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if in_answer and answer_lines:
                answer_lines.append("")
            continue

        question = _extract_question_line(line)
        if question is not None:
            if current_question and answer_lines:
                answer = "\n".join(answer_lines).strip()
                if answer:
                    pairs.append(
                        QAPair(
                            question=current_question,
                            answer=answer,
                            question_type=_qa_question_type(current_question),
                        )
                    )
            current_question = question
            answer_lines = []
            in_answer = False
            continue

        answer = _extract_answer_line(line)
        if answer is not None and current_question:
            in_answer = True
            answer_lines = [answer] if answer else []
            continue

        if current_question:
            if in_answer:
                answer_lines.append(line)
            elif answer_lines:
                answer_lines.append(line)

    if current_question and answer_lines:
        answer = "\n".join(answer_lines).strip()
        if answer:
            pairs.append(
                QAPair(
                    question=current_question,
                    answer=answer,
                    question_type=_qa_question_type(current_question),
                )
            )
    return pairs


def _extract_question_line(line: str) -> str | None:
    match = re.match(r"^(?:#{1,6}\s*)?(?:Q|Question|问题|问)[:：]\s*(.+)$", line, re.I)
    if match:
        return match.group(1).strip()
    return None


def _extract_answer_line(line: str) -> str | None:
    match = re.match(r"^(?:A|Answer|答案|答)[:：]\s*(.*)$", line, re.I)
    if match:
        return match.group(1).strip()
    return None


def _qa_pair_content(pair: QAPair) -> str:
    return f"Question: {pair.question}\nAnswer:\n{pair.answer}"


def _qa_pair_title(document_title: str, pair: QAPair, index: int) -> str:
    question = pair.question[:80].strip()
    return f"{document_title} / Q{index + 1}: {question}" if question else f"{document_title} / Q{index + 1}"


def _qa_question_type(question: str) -> str:
    lowered = question.lower()
    if any(term in lowered for term in ("compare", "difference", "vs", "对比", "区别", "差异")):
        return "comparison"
    if any(term in lowered for term in ("code", "implement", "代码", "实现")):
        return "code"
    if any(term in lowered for term in ("scenario", "case", "场景", "项目")):
        return "scenario"
    if any(term in lowered for term in ("why", "how", "什么", "为什么", "如何", "怎么")):
        return "concept"
    return "fact"


def _trim_text_range(text: str, absolute_start: int, absolute_end: int) -> tuple[int, int, str] | None:
    if not text or not text.strip():
        return None
    leading = len(text) - len(text.lstrip())
    trailing_text = text.rstrip()
    char_start = absolute_start + leading
    char_end = absolute_start + len(trailing_text)
    if char_end < char_start:
        return None
    return char_start, min(char_end, absolute_end), text[leading : len(trailing_text)]


def _dominant_split_level(units: list[TextUnit]) -> str:
    if not units:
        return "unknown"
    first = units[0].split_level
    if all(unit.split_level == first for unit in units):
        return first
    return "mixed"


def _clean_heading(value: str) -> str:
    return value.strip().strip("#").strip()


def _chunk_title(document_title: str, section_title: str | None) -> str:
    if not section_title:
        return document_title
    return f"{document_title} / {section_title}"


def _chunk_metadata(
    *,
    parsed_document: ParsedDocument,
    request: DocumentIngestRequest,
    content: str,
    chunk_strategy: str,
    chunk_level: str,
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    extra_values = extra or {}
    heading_path = _string_list(extra_values.get("heading_path"))
    section_title = _string_value(extra_values.get("section_title"))
    block_type, quality_score, quality_reasons = _classify_block_quality(
        content=content,
        title=parsed_document.title,
        file_type=str(request.file.file_type),
        heading_path=heading_path,
        chunk_level=chunk_level,
    )
    embedding_text = _embedding_text(
        title=parsed_document.title,
        heading_path=heading_path,
        section_title=section_title,
        content=content,
        chunk_level=chunk_level,
    )
    metadata: dict[str, object] = {
        **parsed_document.metadata,
        **request.metadata,
        "knowledge_base_id": request.knowledge_base_id,
        "title": parsed_document.title,
        "document_type": request.document_type,
        "file_type": request.file.file_type,
        "chunk_strategy": chunk_strategy,
        "chunk_level": chunk_level,
        "block_type": block_type,
        "quality_score": quality_score,
        "low_quality_reasons": quality_reasons,
        "embedding_text": embedding_text,
        "embedding_text_mode": "heading-aware",
        "content_preview": content[:600],
        "tags": request.tags,
        "tech_stack": request.tech_stack,
    }
    if extra_values:
        metadata.update({key: value for key, value in extra_values.items() if value is not None})
    return metadata


def _embedding_text(
    *,
    title: str,
    heading_path: list[str],
    section_title: str | None,
    content: str,
    chunk_level: str,
) -> str:
    parts = [f"Document: {title}"]
    if heading_path:
        parts.append("Heading path: " + " > ".join(heading_path))
    elif section_title:
        parts.append(f"Section: {section_title}")
    parts.append(f"Chunk level: {chunk_level}")
    parts.append("Content:")
    parts.append(content)
    return "\n".join(parts)


def _classify_block_quality(
    *,
    content: str,
    title: str,
    file_type: str,
    heading_path: list[str],
    chunk_level: str,
) -> tuple[str, float, list[str]]:
    stripped = content.strip()
    lowered = stripped.lower()
    reasons: list[str] = []
    block_type = "paragraph"
    quality_score = 1.0

    if chunk_level == "parent":
        block_type = "mixed"

    if re.fullmatch(r"(```[\s\S]*```|~~~[\s\S]*~~~)", stripped):
        block_type = "code"
    elif _looks_like_table(stripped):
        block_type = "table"
    elif _looks_like_list(stripped):
        block_type = "list"
    elif _looks_like_image_caption(stripped):
        block_type = "image_caption"
        quality_score = min(quality_score, 0.35)
        reasons.append("image_or_attachment_reference")
    elif _looks_like_toc(stripped, heading_path):
        block_type = "table_of_contents"
        quality_score = min(quality_score, 0.45)
        reasons.append("table_of_contents")

    if _looks_like_prompt_example(stripped, title):
        block_type = "prompt_example" if block_type == "paragraph" else block_type
        quality_score = min(quality_score, 0.65)
        reasons.append("prompt_example")

    if _looks_like_weak_ocr(stripped):
        quality_score = min(quality_score, 0.4)
        reasons.append("weak_ocr_or_symbol_noise")

    if file_type.lower().endswith("image"):
        quality_score = min(quality_score, 0.5)
        reasons.append("image_file_type")

    if len(stripped) < 40 and block_type not in {"code", "table"}:
        quality_score = min(quality_score, 0.7)
        reasons.append("very_short_chunk")

    if "prompt" in lowered and ("example" in lowered or "示例" in stripped):
        quality_score = min(quality_score, 0.75)
        if "prompt_example" not in reasons:
            reasons.append("prompt_example")

    return block_type, round(quality_score, 3), reasons


def _looks_like_table(content: str) -> bool:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    pipe_lines = sum(1 for line in lines if line.count("|") >= 2)
    return pipe_lines >= 2 or any(re.fullmatch(r"[-:| ]{6,}", line) for line in lines)


def _looks_like_list(content: str) -> bool:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if len(lines) < 2:
        return False
    list_lines = sum(1 for line in lines if re.match(r"^([-*+]|\d+[.)])\s+", line))
    return list_lines / len(lines) >= 0.6


def _looks_like_image_caption(content: str) -> bool:
    image_refs = re.findall(r"!\[[^\]]*]\([^)]+\)|!\[\[[^\]]+]]|\[\[[^\]]+\.(?:png|jpg|jpeg|gif|webp|svg)]]", content, re.I)
    if not image_refs:
        return False
    text_without_refs = re.sub(r"!\[[^\]]*]\([^)]+\)|!\[\[[^\]]+]]|\[\[[^\]]+\.(?:png|jpg|jpeg|gif|webp|svg)]]", "", content, flags=re.I).strip()
    return len(text_without_refs) < 80


def _looks_like_toc(content: str, heading_path: list[str]) -> bool:
    lowered_headings = " ".join(heading_path).lower()
    if any(term in lowered_headings for term in ("目录", "table of contents", "toc")):
        return True
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if len(lines) < 4:
        return False
    link_like = sum(1 for line in lines if re.search(r"\[[^\]]+]\([^)]+\)|\[\[[^\]]+]]|^#{1,6}\s+", line))
    return link_like / len(lines) >= 0.7


def _looks_like_prompt_example(content: str, title: str) -> bool:
    combined = f"{title}\n{content}".lower()
    markers = [
        "-goal-",
        "-steps-",
        "few-shot",
        "example input",
        "example output",
        "output:",
        "you are an ai assistant",
        "prompts/",
    ]
    marker_hits = sum(1 for marker in markers if marker in combined)
    return marker_hits >= 2 or "extract_graph" in combined or "community_report" in combined


def _looks_like_weak_ocr(content: str) -> bool:
    if len(content) < 80:
        return False
    visible = [char for char in content if not char.isspace()]
    if not visible:
        return True
    symbol_count = sum(1 for char in visible if not char.isalnum() and not "\u4e00" <= char <= "\u9fff")
    replacement_count = content.count("�")
    return replacement_count >= 3 or symbol_count / len(visible) > 0.45


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _string_value(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _bounded_int(value: object, *, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if parsed < minimum:
        return minimum
    if parsed > maximum:
        return maximum
    return parsed
