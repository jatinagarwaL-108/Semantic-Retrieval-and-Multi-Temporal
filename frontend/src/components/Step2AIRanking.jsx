import React from "react";
import { Sparkles, MapPin, Layers, ArrowRight, BrainCircuit, CheckCircle2, ShieldCheck } from "lucide-react";

export default function Step2AIRanking({
  query,
  understanding,
  searchResults,
  isSearching,
  onSelectCandidate,
}) {
  return (
    <div style={{ maxWidth: "1120px", margin: "28px auto", padding: "0 20px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px" }}>
        <div>
          <span className="badge-tag badge-cyan" style={{ marginBottom: "6px" }}>
            Step 2 • Semantic Vector Retrieval
          </span>
          <h2 style={{ fontSize: "1.6rem", fontWeight: 700, color: "#f8fafc" }}>
            RemoteCLIP AI Query Understanding & Candidate Ranking
          </h2>
        </div>
        <div style={{ textAlign: "right" }}>
          <span style={{ fontSize: "0.78rem", color: "#94a3b8" }}>ANN Vector Database:</span>
          <div style={{ display: "flex", alignItems: "center", gap: "6px", justifyContent: "flex-end" }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#10b981" }} />
            <strong style={{ fontSize: "0.82rem", color: "#34d399" }}>FAISS / Milvus-Compatible</strong>
          </div>
        </div>
      </div>

      {/* Query Understanding State Panel */}
      <div className="tactical-panel" style={{ padding: "20px", marginBottom: "28px", borderLeft: "4px solid #38bdf8" }}>
        <div style={{ display: "flex", alignItems: "flex-start", gap: "14px" }}>
          <div style={{
            width: 38,
            height: 38,
            borderRadius: "8px",
            background: "rgba(56, 189, 248, 0.15)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}>
            <BrainCircuit size={22} color="#38bdf8" />
          </div>

          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
              <span style={{ fontSize: "0.78rem", color: "#94a3b8", fontWeight: 600 }}>Active Query:</span>
              <span style={{
                background: "rgba(15, 23, 42, 0.8)",
                padding: "2px 10px",
                borderRadius: "4px",
                color: "#f8fafc",
                fontSize: "0.9rem",
                fontWeight: 600,
                border: "1px solid #334155",
              }}>
                "{query}"
              </span>
              <span className="badge-tag badge-emerald">
                <CheckCircle2 size={12} /> Semantic Embedding Projected (512-dim)
              </span>
            </div>

            {understanding && (
              <div style={{ marginTop: "12px", display: "flex", gap: "16px", flexWrap: "wrap", fontSize: "0.78rem", color: "#94a3b8" }}>
                <div>
                  <span style={{ color: "#64748b" }}>Detected Domain Concepts: </span>
                  <strong style={{ color: "#38bdf8" }}>
                    {understanding.detected_domain_concepts?.join(", ") || "construction, water body, infrastructure"}
                  </strong>
                </div>
                <div>
                  <span style={{ color: "#64748b" }}>Retrieval Strategy: </span>
                  <strong style={{ color: "#cbd5e1" }}>{understanding.retrieval_strategy || "ViT-B Cosine ANN"}</strong>
                </div>
                <div>
                  <span style={{ color: "#64748b" }}>Candidate Tiles Evaluated: </span>
                  <strong style={{ color: "#fbbf24" }}>{searchResults.length}</strong>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isSearching && (
        <div style={{ textAlign: "center", padding: "60px 0" }}>
          <div style={{
            width: 48,
            height: 48,
            border: "4px solid rgba(56, 189, 248, 0.2)",
            borderTopColor: "#38bdf8",
            borderRadius: "50%",
            margin: "0 auto 16px",
            animation: "spin 1s linear infinite",
          }} />
          <h3 style={{ fontSize: "1.1rem", color: "#e2e8f0" }}>Understanding query & computing vector cosine similarities...</h3>
          <p style={{ fontSize: "0.82rem", color: "#64748b", marginTop: "4px" }}>Scanning air-gapped Sentinel-2 tile embeddings in Milvus/FAISS store</p>
        </div>
      )}

      {/* Ranked Candidate Results */}
      {!isSearching && (
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
          gap: "20px",
        }}>
          {searchResults.map((item, idx) => {
            const meta = item.metadata || {};
            const scorePct = (item.similarity_score * 100).toFixed(1);
            const isTopMatch = idx === 0;

            return (
              <div
                key={item.tile_id || idx}
                className="tactical-card"
                style={{
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  borderColor: isTopMatch ? "rgba(56, 189, 248, 0.6)" : "var(--border-color)",
                  position: "relative",
                  background: isTopMatch
                    ? "linear-gradient(180deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%)"
                    : "rgba(30, 41, 59, 0.4)",
                }}
              >
                {/* Top Badge */}
                {isTopMatch && (
                  <div style={{
                    position: "absolute",
                    top: "-10px",
                    right: "14px",
                    background: "linear-gradient(90deg, #0284c7, #2563eb)",
                    color: "#fff",
                    fontSize: "0.68rem",
                    fontWeight: 700,
                    padding: "2px 8px",
                    borderRadius: "4px",
                    boxShadow: "0 0 10px rgba(14, 165, 233, 0.5)",
                  }}>
                    TOP RANKED MATCH
                  </div>
                )}

                <div>
                  {/* Thumbnail Preview & Score Overlay */}
                  <div style={{
                    position: "relative",
                    width: "100%",
                    height: "170px",
                    borderRadius: "6px",
                    overflow: "hidden",
                    marginBottom: "14px",
                    background: "#0f172a",
                    border: "1px solid rgba(51, 65, 85, 0.6)",
                  }}>
                    <img
                      src={`http://localhost:8000/api/tiles/${item.tile_id}/preview`}
                      alt={item.tile_id}
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                      style={{ width: "100%", height: "100%", objectFit: "cover" }}
                    />

                    {/* Rank Badge */}
                    <div style={{
                      position: "absolute",
                      top: "8px",
                      left: "8px",
                      background: "rgba(15, 23, 42, 0.85)",
                      color: "#f8fafc",
                      border: "1px solid rgba(255, 255, 255, 0.2)",
                      borderRadius: "4px",
                      padding: "2px 8px",
                      fontSize: "0.75rem",
                      fontWeight: 700,
                    }}>
                      Rank #{item.rank}
                    </div>

                    {/* Cosine Similarity Score */}
                    <div style={{
                      position: "absolute",
                      bottom: "8px",
                      right: "8px",
                      background: "rgba(15, 23, 42, 0.9)",
                      border: "1px solid #10b981",
                      borderRadius: "6px",
                      padding: "4px 8px",
                      display: "flex",
                      alignItems: "center",
                      gap: "4px",
                    }}>
                      <Sparkles size={12} color="#34d399" />
                      <strong style={{ fontSize: "0.85rem", color: "#34d399" }}>{scorePct}%</strong>
                      <span style={{ fontSize: "0.68rem", color: "#94a3b8" }}>match</span>
                    </div>
                  </div>

                  {/* Tile ID & Acquisition Date */}
                  <h4 style={{ fontSize: "0.88rem", fontWeight: 700, color: "#f8fafc", wordBreak: "break-all" }}>
                    {item.tile_id}
                  </h4>
                  <div style={{ fontSize: "0.74rem", color: "#94a3b8", marginTop: "4px" }}>
                    Acquired: {meta.acquisition_date || "2026-02-20"} • {meta.parent_scene_id || "Sentinel-2 L2A"}
                  </div>

                  {/* Geospatial Coordinates */}
                  {meta.bounds && (
                    <div style={{
                      marginTop: "10px",
                      background: "rgba(15, 23, 42, 0.6)",
                      padding: "6px 8px",
                      borderRadius: "4px",
                      fontSize: "0.7rem",
                      color: "#64748b",
                      fontFamily: "monospace",
                    }}>
                      Easting: {Math.round(meta.bounds[0])} → {Math.round(meta.bounds[2])} | Northing: {Math.round(meta.bounds[1])}
                    </div>
                  )}
                </div>

                {/* Action Button */}
                <button
                  onClick={() => onSelectCandidate(item)}
                  className="tactical-btn btn-primary"
                  style={{
                    width: "100%",
                    marginTop: "16px",
                    justifyContent: "center",
                    padding: "10px",
                    fontSize: "0.84rem",
                  }}
                >
                  <span>Inspect & Detect Change</span>
                  <ArrowRight size={15} />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
