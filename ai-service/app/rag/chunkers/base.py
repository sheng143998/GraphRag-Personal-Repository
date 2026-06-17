from __future__ import annotations

import re
from dataclasses import dataclass
from uuid import uuid4

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


_HEADING_RE = re.compile(r"(?m)^(#{1,6})\s+(.+?)\s*$")
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
                chunks.append(child.copy(update={"chunk_index": chunk_index}))
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
    return parent_segments


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
    return _merge_short_segments(
        source_text=source_text,
        segments=segments,
        min_chunk_size=min_chunk_size,
        max_chunk_size=chunk_size,
    )


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
    metadata: dict[str, object] = {
        **parsed_document.metadata,
        **request.metadata,
        "knowledge_base_id": request.knowledge_base_id,
        "title": parsed_document.title,
        "document_type": request.document_type,
        "file_type": request.file.file_type,
        "chunk_strategy": chunk_strategy,
        "chunk_level": chunk_level,
        "content_preview": content[:600],
        "tags": request.tags,
        "tech_stack": request.tech_stack,
    }
    if extra:
        metadata.update({key: value for key, value in extra.items() if value is not None})
    return metadata


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
