import { useEffect, useMemo, useState } from "react";
import { fetchGraphFacts, fetchKnowledgeBases } from "../api";
import type { GraphEntityFact, GraphFactsResponse, GraphRelationshipFact, KnowledgeBaseSummary } from "../types";
import "./graph-page.css";

interface GraphNode extends GraphEntityFact {
  x: number;
  y: number;
  radius: number;
}

const emptyGraph: GraphFactsResponse = {
  knowledgeBaseId: "",
  entityCount: 0,
  relationshipCount: 0,
  entities: [],
  relationships: []
};

export function GraphPage(): JSX.Element {
  const [knowledgeBases, setKnowledgeBases] = useState<KnowledgeBaseSummary[]>([]);
  const [knowledgeBaseId, setKnowledgeBaseId] = useState("");
  const [entityQuery, setEntityQuery] = useState("");
  const [graph, setGraph] = useState<GraphFactsResponse>(emptyGraph);
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const nodes = useMemo(() => layoutNodes(graph.entities), [graph.entities]);
  const selectedNode = nodes.find((item) => item.id === selectedId) ?? nodes[0];
  const visibleRelationships = graph.relationships.slice(0, 36);

  async function load(nextKnowledgeBaseId = knowledgeBaseId, nextEntity = entityQuery) {
    if (!nextKnowledgeBaseId) return;
    setLoading(true);
    setError("");
    try {
      const facts = await fetchGraphFacts(nextKnowledgeBaseId, nextEntity);
      setGraph(facts);
      setSelectedId((current) => current || facts.entities[0]?.id || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "无法加载知识图谱事实。");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void fetchKnowledgeBases()
      .then((items) => {
        setKnowledgeBases(items);
        const firstId = items[0]?.id ?? "";
        setKnowledgeBaseId(firstId);
        if (firstId) void load(firstId, "");
      })
      .catch((err) => setError(err instanceof Error ? err.message : "无法加载知识库列表。"));
  }, []);

  return (
    <div className="graph-workbench">
      <section className="graph-canvas-panel">
        <div className="graph-toolbar">
          <label className="graph-field">
            <span className="material-symbols-outlined">database</span>
            <select value={knowledgeBaseId} onChange={(event) => {
              setKnowledgeBaseId(event.target.value);
              void load(event.target.value, entityQuery);
            }}>
              {knowledgeBases.map((item) => (
                <option key={item.id} value={item.id}>{item.name}</option>
              ))}
            </select>
          </label>
          <label className="graph-field graph-search">
            <span className="material-symbols-outlined">search</span>
            <input
              value={entityQuery}
              onChange={(event) => setEntityQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") void load();
              }}
              placeholder="Search entity..."
            />
          </label>
          <button className="graph-tool-button primary" type="button" onClick={() => void load()} disabled={loading || !knowledgeBaseId}>
            <span className="material-symbols-outlined">travel_explore</span>
            Explore
          </button>
          <button className="graph-tool-button" type="button">
            <span className="material-symbols-outlined">center_focus_strong</span>
          </button>
          <button className="graph-tool-button" type="button">
            <span className="material-symbols-outlined">account_tree</span>
          </button>
        </div>

        <div className="graph-canvas">
          {error ? <div className="graph-error">{error}</div> : null}
          {nodes.length ? (
            <svg viewBox="0 0 1000 640" role="img" aria-label="Knowledge graph">
              <defs>
                <filter id="nodeShadow" x="-20%" y="-20%" width="140%" height="140%">
                  <feDropShadow dx="0" dy="8" stdDeviation="10" floodColor="#191c1e" floodOpacity="0.12" />
                </filter>
              </defs>
              <GraphLinks nodes={nodes} relationships={visibleRelationships} />
              {nodes.map((node) => (
                <g
                  className={`graph-node${selectedNode?.id === node.id ? " is-selected" : ""}`}
                  key={node.id}
                  onClick={() => setSelectedId(node.id)}
                  transform={`translate(${node.x} ${node.y})`}
                >
                  <circle r={node.radius} />
                  <text textAnchor="middle" y="-2">{node.name.slice(0, 16)}</text>
                  <text className="node-type" textAnchor="middle" y="15">{node.entityType || "Entity"}</text>
                </g>
              ))}
            </svg>
          ) : (
            <div className="graph-empty">
              <span className="material-symbols-outlined">account_tree</span>
              <strong>{loading ? "正在加载图谱事实" : "暂无图谱事实"}</strong>
              <p>上传并解析文档后，GraphRAG 实体和关系会在这里形成可探索画布。</p>
            </div>
          )}
        </div>

        <div className="graph-status">
          <span>实体：{graph.entityCount}</span>
          <span>关系：{graph.relationshipCount}</span>
          <span>布局：径向固定</span>
          <span>来源：图谱事实接口</span>
        </div>
      </section>

      <aside className="graph-detail">
        <section className="graph-side-card">
          <div className="graph-side-head">
            <h2>实体详情</h2>
            <span className="material-symbols-outlined">close</span>
          </div>
          {selectedNode ? (
            <div className="entity-detail">
              <div className="entity-avatar">{selectedNode.name.slice(0, 1).toUpperCase()}</div>
              <h3>{selectedNode.name}</h3>
              <span>{selectedNode.entityType || "实体"}</span>
              <dl>
                <dt>标准名称</dt>
                <dd>{selectedNode.normalizedName}</dd>
                <dt>文档</dt>
                <dd>{selectedNode.documentId || "--"}</dd>
                <dt>片段</dt>
                <dd>{selectedNode.chunkId || "--"}</dd>
              </dl>
            </div>
          ) : (
            <div className="graph-panel-empty">选择节点后查看元数据。</div>
          )}
        </section>

        <section className="graph-side-card">
          <div className="graph-side-head">
            <h2>Relationship Explorer</h2>
            <span>{visibleRelationships.length}</span>
          </div>
          <div className="relationship-list">
            {visibleRelationships.map((item) => (
              <RelationshipItem item={item} key={item.id} />
            ))}
            {!visibleRelationships.length ? <div className="graph-panel-empty">暂无关系数据。</div> : null}
          </div>
        </section>

        <section className="graph-side-card">
          <div className="graph-side-head">
            <h2>Legend</h2>
          </div>
          <div className="graph-legend">
            <span><i className="entity" /> Entity node</span>
            <span><i className="selected" /> Selected node</span>
            <span><i className="link" /> Relationship edge</span>
          </div>
        </section>
      </aside>
    </div>
  );
}

function layoutNodes(entities: GraphEntityFact[]): GraphNode[] {
  if (!entities.length) return [];
  const limited = entities.slice(0, 28);
  const centerX = 500;
  const centerY = 320;
  return limited.map((entity, index) => {
    const ring = index < 1 ? 0 : index < 9 ? 1 : 2;
    const ringIndex = ring === 0 ? 0 : index - (ring === 1 ? 1 : 9);
    const ringCount = ring === 0 ? 1 : ring === 1 ? 8 : Math.max(1, limited.length - 9);
    const angle = ring === 0 ? 0 : (Math.PI * 2 * ringIndex) / ringCount - Math.PI / 2;
    const distance = ring === 0 ? 0 : ring === 1 ? 155 : 255;
    return {
      ...entity,
      x: centerX + Math.cos(angle) * distance,
      y: centerY + Math.sin(angle) * distance,
      radius: ring === 0 ? 48 : ring === 1 ? 38 : 30
    };
  });
}

function GraphLinks({ nodes, relationships }: { nodes: GraphNode[]; relationships: GraphRelationshipFact[] }) {
  const byName = new Map(nodes.flatMap((node) => [[node.name, node], [node.normalizedName, node]]));
  const fallbackCenter = nodes[0];
  return (
    <g className="graph-links">
      {relationships.map((relationship, index) => {
        const source = byName.get(relationship.sourceName) ?? fallbackCenter;
        const target = byName.get(relationship.targetName) ?? nodes[(index % Math.max(1, nodes.length - 1)) + 1] ?? fallbackCenter;
        if (!source || !target || source.id === target.id) return null;
        return (
          <g key={relationship.id}>
            <line x1={source.x} y1={source.y} x2={target.x} y2={target.y} />
            <text x={(source.x + target.x) / 2} y={(source.y + target.y) / 2}>{relationship.relationType.slice(0, 14)}</text>
          </g>
        );
      })}
    </g>
  );
}

function RelationshipItem({ item }: { item: GraphRelationshipFact }) {
  return (
    <article className="relationship-item">
      <strong>{item.sourceName}</strong>
      <span>{item.relationType}</span>
      <strong>{item.targetName}</strong>
      <small>confidence {Math.round((item.confidence ?? 0) * 100)}%</small>
    </article>
  );
}
