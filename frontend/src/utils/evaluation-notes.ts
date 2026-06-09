import type { ExperimentEvaluationHistory } from "../types";

export interface GraphRagMetricNote {
  entityCoverage: number;
  relationshipHit: number;
  expansionTermHit: number;
}

const GRAPH_NOTE_PATTERN =
  /GraphRAG (?:metadata scored|元数据指标：)entity_coverage=([0-9.]+), relationship_hit=([0-9.]+), expansion_term_hit=([0-9.]+)[.。]/;

export function parseGraphRagMetricNote(notes?: string | null): GraphRagMetricNote | null {
  if (!notes) return null;
  const match = notes.match(GRAPH_NOTE_PATTERN);
  if (!match) return null;
  return {
    entityCoverage: Number(match[1]),
    relationshipHit: Number(match[2]),
    expansionTermHit: Number(match[3])
  };
}

export function hasGraphRagMetricNote(evaluation: ExperimentEvaluationHistory): boolean {
  return parseGraphRagMetricNote(evaluation.notes) !== null;
}

export function formatMetricPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}
