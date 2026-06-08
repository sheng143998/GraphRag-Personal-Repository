from __future__ import annotations

import re
from dataclasses import dataclass, field


_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "should",
    "the",
    "to",
    "use",
    "uses",
    "what",
    "when",
    "with",
}


@dataclass(frozen=True)
class GraphEntity:
    name: str
    entity_type: str = "concept"
    aliases: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GraphRelationship:
    source: str
    target: str
    relation_type: str = "co_occurs_with"
    confidence: float = 0.5


class RuleBasedGraphExtractor:
    def extract_entities(self, text: str, *, max_entities: int = 8) -> list[GraphEntity]:
        candidates = _candidate_terms(text)
        entities: list[GraphEntity] = []
        seen: set[str] = set()
        for candidate in candidates:
            key = candidate.lower()
            if key in seen or key in _STOP_WORDS:
                continue
            seen.add(key)
            entity_type = "technology" if any(char.isupper() for char in candidate) else "concept"
            entities.append(GraphEntity(name=candidate, entity_type=entity_type, aliases=(key,)))
            if len(entities) >= max_entities:
                break
        return entities

    def extract_relationships(self, entities: list[GraphEntity]) -> list[GraphRelationship]:
        relationships: list[GraphRelationship] = []
        for index, source in enumerate(entities):
            for target in entities[index + 1 : index + 3]:
                relationships.append(
                    GraphRelationship(
                        source=source.name,
                        target=target.name,
                        confidence=round(0.8 - (index * 0.03), 3),
                    )
                )
        return relationships

    def augment_query(self, query: str, entities: list[GraphEntity]) -> str:
        terms = [entity.name for entity in entities if entity.name.lower() not in query.lower()]
        if not terms:
            return query
        return f"{query} {' '.join(terms[:5])}"


def _candidate_terms(text: str) -> list[str]:
    phrase_matches = re.findall(r"\b[A-Z][A-Za-z0-9]*(?:[- ][A-Z]?[A-Za-z0-9]+){0,2}\b", text)
    token_matches = re.findall(r"\b[A-Za-z][A-Za-z0-9_-]{2,}\b", text)
    candidates = phrase_matches + token_matches
    return [candidate.strip(" -_") for candidate in candidates if candidate.strip(" -_")]
