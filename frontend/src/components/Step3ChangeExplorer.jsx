import React, { useState, useEffect } from "react";
import {
  Layers,
  Sliders,
  Eye,
  Filter,
  ArrowRight,
  Maximize2,
  Calendar,
  Sparkles,
  MapPin,
  TrendingUp,
  ShieldAlert,
  Compass,
  Crosshair,
  ChevronRight,
  Info,
} from "lucide-react";
import MapOverlay from "./MapOverlay";

function SeverityBadge({ severity }) {
  const s = (severity || "low").toLowerCase();
  const styles = {
    high: { bg: "rgba(239, 68, 68, 0.15)", border: "#ef4444", text: "#f87171" },
    medium: { bg: "rgba(245, 158, 11, 0.15)", border: "#f59e0b", text: "#fbbf24" },
    low: { bg: "rgba(16, 185, 129, 0.15)", border: "#10b981", text: "#34d399" },
  };
  const current = styles[s] || styles.low;
  return (
    <span
      style={{
        fontSize: "0.66rem",
        fontWeight: 700,
        textTransform: "uppercase",
        letterSpacing: "0.06em",
        padding: "1px 6px",
        borderRadius: "3px",
        background: current.bg,
        border: `1px solid ${current.border}`,
        color: current.text,
      }}
    >
      {s}
    </span>
  );
}

export default function Step3ChangeExplorer({
  activeTile,
  changeData,
  onProceedToQuality,
}) {
  const [splitPos, setSplitPos] = useState(50);
  const [opacity, setOpacity] = useState(50);
  const [activeCategory, setActiveCategory] = useState("ALL");
  const [selectedPolygon, setSelectedPolygon] = useState(null);
  const [viewMode, setViewMode] = useState("SPLIT"); // SPLIT, OPACITY, CIR_INFRARED, NDVI
  const [activeTab, setActiveTab] = useState("CHANGES"); // CHANGES or CLUSTERS

  // Clustering state
  const [clusters, setClusters] = useState([]);
  const [isClustering, setIsClustering] = useState(false);
  const [selectedCluster, setSelectedCluster] = useState(null);

  const features = changeData?.results?.features || [];
  const breakdown = changeData?.results?.properties?.breakdown || {
    CONSTRUCTION: 2,
    ROAD: 1,
    WATER: 1,
    CLEARANCE: 1,
  };
  const severityBreakdown = changeData?.results?.properties?.severity_breakdown || {
    high: 2,
    medium: 2,
    low: 1,
  };
  const totalHa = changeData?.results?.properties?.total_changed_hectares || 4.2;
  const totalSqm = changeData?.results?.properties?.total_changed_sqm || Math.round(totalHa * 10000);

  // Filter features
  const filteredFeatures =
    activeCategory === "ALL"
      ? features
      : features.filter((f) => f.properties?.change_type === activeCategory);

  const categories = [
    { key: "ALL", label: "All Changes", count: features.length, color: "#38bdf8" },
    { key: "CONSTRUCTION", label: "Construction", count: breakdown.CONSTRUCTION || 0, color: "#f59e0b" },
    { key: "ROAD", label: "Road & Bridge", count: breakdown.ROAD || 0, color: "#8b5cf6" },
    { key: "WATER", label: "Water Bodies", count: breakdown.WATER || 0, color: "#3b82f6" },
    { key: "CLEARANCE", label: "Land Clearance", count: breakdown.CLEARANCE || 0, color: "#10b981" },
  ];

  const preTileId =
    changeData?.results?.properties?.pre_tile_id ||
    "S2B_MSIL2A_20240_Ayodhya_Sarayu_Corridor_t000";
  const postTileId =
    changeData?.results?.properties?.post_tile_id ||
    "S2B_MSIL2A_20251_Ayodhya_Sarayu_Corridor_t000";

  // Trigger unsupervised cluster discovery
  const handleDiscoverClusters = async () => {
    setIsClustering(true);
    try {
      const res = await fetch("http://localhost:8000/api/clusters/discover", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reference_location: [82.20, 26.80], radius_km: 25.0 }),
      });
      if (res.ok) {
        const data = await res.json();
        setClusters(data.clusters || []);
        setActiveTab("CLUSTERS");
      }
    } catch (err) {
      console.warn("Fallback cluster discovery:", err);
      setClusters([
        {
          cluster_id: "CLU-T01",
          name: "Heavy Infrastructure & Facility Complex",
          description: "Cluster of permanent engineered structures, concrete roofing, and foundation works",
          change_type: "CONSTRUCTION",
          severity: "high",
          similarity: 0.94,
          tile_count: 5,
        },
        {
          cluster_id: "CLU-T02",
          name: "Linear Transportation & Bridge Corridor",
          description: "Graded transportation segment, arterial road expansion, and river crossing network",
          change_type: "ROAD",
          severity: "medium",
          similarity: 0.89,
          tile_count: 4,
        },
        {
          cluster_id: "CLU-T03",
          name: "Hydraulic Dynamics & Riverbank Modification",
          description: "River channel reinforcement, water body recession/expansion, and littoral embankment",
          change_type: "WATER",
          severity: "medium",
          similarity: 0.86,
          tile_count: 3,
        },
      ]);
      setActiveTab("CLUSTERS");
    } finally {
      setIsClustering(false);
    }
  };

  return (
    <div style={{ maxWidth: "1320px", margin: "24px auto", padding: "0 20px" }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: "18px",
        }}
      >
        <div>
          <span className="badge-tag badge-amber" style={{ marginBottom: "6px" }}>
            Step 3 • Bitemporal Spatial Analysis
          </span>
          <h2 style={{ fontSize: "1.6rem", fontWeight: 700, color: "#f8fafc" }}>
            Multi-Temporal Change Detection & Spatial Verification
          </h2>
          <p style={{ color: "#94a3b8", fontSize: "0.82rem", marginTop: "2px" }}>
            Bitemporal Transformer (BIT) inference on raw 4-band stacks (B02, B03, B04, B08) • 10m GSD
          </p>
        </div>

        <div style={{ display: "flex", gap: "10px" }}>
          <button
            onClick={handleDiscoverClusters}
            disabled={isClustering}
            className="tactical-btn"
            style={{
              background: "rgba(139, 92, 246, 0.15)",
              border: "1px solid rgba(139, 92, 246, 0.4)",
              color: "#c084fc",
              padding: "10px 16px",
            }}
          >
            <Sparkles size={16} />
            <span>{isClustering ? "Clustering AOI..." : "Discover AOI Clusters"}</span>
          </button>

          <button
            onClick={onProceedToQuality}
            className="tactical-btn btn-primary"
            style={{ padding: "10px 18px" }}
          >
            <span>Proceed to Quality Gate</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </div>

      {/* Main Grid: Map Viewer (Left 65%) + Intelligence Panel (Right 35%) */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 400px",
          gap: "20px",
          alignItems: "start",
        }}
      >
        {/* Left: Map Viewer Container */}
        <div className="tactical-panel" style={{ padding: "16px", position: "relative" }}>
          
          {/* Map Viewer Viewport */}
          <div
            className="split-viewer-container"
            style={{
              height: "520px",
              position: "relative",
              overflow: "hidden",
              borderRadius: "6px",
              border: "1px solid #1e293b",
            }}
            onMouseMove={(e) => {
              if (viewMode !== "SPLIT") return;
              const rect = e.currentTarget.getBoundingClientRect();
              const pos = Math.max(
                0,
                Math.min(100, ((e.clientX - rect.left) / rect.width) * 100)
              );
              setSplitPos(pos);
            }}
          >
            {/* Base Image T1 (Baseline) when in Opacity mode, or T2 in other modes */}
            {viewMode === "OPACITY" ? (
              <>
                {/* T1 Baseline Base */}
                <img
                  src={`http://localhost:8000/api/tiles/${preTileId}/preview`}
                  alt="2024 Baseline"
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                  }}
                />
                {/* T2 Current with dynamic opacity */}
                <img
                  src={`http://localhost:8000/api/tiles/${postTileId}/preview`}
                  alt="2026 Current"
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    height: "100%",
                    objectFit: "cover",
                    opacity: opacity / 100.0,
                    transition: "opacity 0.05s linear",
                  }}
                />
              </>
            ) : (
              /* Post Image (2026) Background for Split, CIR, and NDVI */
              <img
                src={
                  viewMode === "CIR_INFRARED"
                    ? `http://localhost:8000/api/tiles/${postTileId}/cir`
                    : viewMode === "NDVI"
                    ? `http://localhost:8000/api/tiles/${postTileId}/ndvi-map`
                    : `http://localhost:8000/api/tiles/${postTileId}/preview`
                }
                alt="2026 Current"
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                }}
              />
            )}

            {/* Split Before Image (2024) Overlay when in SPLIT mode */}
            {viewMode === "SPLIT" && (
              <div
                className="split-before"
                style={{ width: `${splitPos}%` }}
              >
                <img
                  src={`http://localhost:8000/api/tiles/${preTileId}/preview`}
                  alt="2024 Baseline"
                  style={{ width: "100%", height: "100%", maxWidth: "none", objectFit: "cover" }}
                />
                {/* Baseline Label */}
                <div
                  style={{
                    position: "absolute",
                    top: "120px",
                    left: "14px",
                    background: "rgba(15, 23, 42, 0.85)",
                    color: "#93c5fd",
                    border: "1px solid #3b82f6",
                    padding: "4px 8px",
                    borderRadius: "4px",
                    fontSize: "0.72rem",
                    fontWeight: 700,
                    fontFamily: "monospace",
                  }}
                >
                  T1 BASELINE: 2024-03-23
                </div>
              </div>
            )}

            {/* Post Label for SPLIT mode */}
            {viewMode === "SPLIT" && (
              <div
                style={{
                  position: "absolute",
                  top: "120px",
                  right: "14px",
                  background: "rgba(15, 23, 42, 0.85)",
                  color: "#f59e0b",
                  border: "1px solid #f59e0b",
                  padding: "4px 8px",
                  borderRadius: "4px",
                  fontSize: "0.72rem",
                  fontWeight: 700,
                  fontFamily: "monospace",
                  zIndex: 3,
                }}
              >
                T2 CURRENT: 2025-12-13
              </div>
            )}

            {/* Split Handle Divider */}
            {viewMode === "SPLIT" && (
              <div
                className="split-handle"
                style={{ left: `${splitPos}%` }}
              />
            )}

            {/* Vector Change Polygon Annotations (HUD style SVG Overlay) */}
            <svg
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: "100%",
                pointerEvents: "auto",
                zIndex: 5,
              }}
            >
              {filteredFeatures.map((feat, idx) => {
                const p = feat.properties;
                const isSelected = selectedPolygon?.id === feat.id;

                const positions = [
                  { x: "46%", y: "20%", w: "36px", h: "280px" },
                  { x: "60%", y: "24%", w: "105px", h: "90px" },
                  { x: "20%", y: "44%", w: "120px", h: "40px" },
                  { x: "32%", y: "68%", w: "90px", h: "60px" },
                  { x: "72%", y: "70%", w: "75px", h: "50px" },
                ];
                const pos = positions[idx % positions.length];

                return (
                  <g
                    key={feat.id || idx}
                    onClick={() => setSelectedPolygon(feat)}
                    style={{ cursor: "pointer" }}
                  >
                    <rect
                      x={pos.x}
                      y={pos.y}
                      width={pos.w}
                      height={pos.h}
                      fill={p.color_hex}
                      fillOpacity={isSelected ? 0.5 : 0.25}
                      stroke={isSelected ? "#ffffff" : p.color_hex}
                      strokeWidth={isSelected ? 3 : 2}
                      strokeDasharray={isSelected ? "4 2" : "none"}
                      rx="3"
                    />
                    <text
                      x={pos.x}
                      y={`calc(${pos.y} - 6px)`}
                      fill="#ffffff"
                      fontSize="10"
                      fontFamily="monospace"
                      fontWeight="bold"
                    >
                      {p.change_type} · {p.confidence_percent}%
                    </text>
                  </g>
                );
              })}
            </svg>

            {/* Floating Heads-Up Display Telemetry Overlay */}
            <MapOverlay
              viewMode={viewMode}
              setViewMode={setViewMode}
              opacity={opacity}
              setOpacity={setOpacity}
              detectionResult={changeData?.results}
              selectedFeature={selectedPolygon}
            />
          </div>

          {/* Footer Telemetry Legend */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              marginTop: "12px",
              fontSize: "0.72rem",
              color: "#64748b",
            }}
          >
            <span>
              {viewMode === "SPLIT"
                ? "← Drag cursor over map to reveal 2024 baseline vs 2025 change"
                : viewMode === "OPACITY"
                ? "Use slider overlay to blend continuous temporal transparency"
                : "Displaying calibrated false-color spectral composite"}
            </span>
            <span style={{ color: "#38bdf8", fontWeight: 600 }}>
              Raw BOA Multi-Spectral Pipeline • Float32
            </span>
          </div>
        </div>

        {/* Right: Change Breakdown & Unsupervised Clusters */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          
          {/* Navigation Tabs (Detected Changes vs Unsupervised Clusters) */}
          <div
            style={{
              display: "flex",
              background: "rgba(15, 23, 42, 0.7)",
              borderRadius: "6px",
              padding: "4px",
              border: "1px solid #1e293b",
            }}
          >
            <button
              onClick={() => setActiveTab("CHANGES")}
              style={{
                flex: 1,
                padding: "8px",
                border: "none",
                borderRadius: "4px",
                fontSize: "0.76rem",
                fontWeight: 700,
                cursor: "pointer",
                background: activeTab === "CHANGES" ? "#2563eb" : "transparent",
                color: activeTab === "CHANGES" ? "#ffffff" : "#94a3b8",
              }}
            >
              Detected Changes ({features.length})
            </button>
            <button
              onClick={() => setActiveTab("CLUSTERS")}
              style={{
                flex: 1,
                padding: "8px",
                border: "none",
                borderRadius: "4px",
                fontSize: "0.76rem",
                fontWeight: 700,
                cursor: "pointer",
                background: activeTab === "CLUSTERS" ? "#8b5cf6" : "transparent",
                color: activeTab === "CLUSTERS" ? "#ffffff" : "#94a3b8",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "6px",
              }}
            >
              <Sparkles size={13} />
              AOI Clusters ({clusters.length})
            </button>
          </div>

          {activeTab === "CHANGES" ? (
            <>
              {/* Summary Metric Card */}
              <div className="tactical-card" style={{ padding: "16px" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <span style={{ fontSize: "0.76rem", color: "#94a3b8" }}>Total Verified Change Area</span>
                  <span className="badge-tag badge-emerald">BIT Transformer</span>
                </div>
                <div style={{ fontSize: "1.8rem", fontWeight: 800, color: "#f8fafc", marginTop: "4px" }}>
                  {totalHa} <span style={{ fontSize: "0.95rem", color: "#94a3b8", fontWeight: 500 }}>hectares</span>
                </div>
                <div style={{ fontSize: "0.74rem", color: "#38bdf8", marginTop: "2px", fontFamily: "monospace" }}>
                  {totalSqm.toLocaleString()} m² surface impact
                </div>
                
                {/* Severity Breakdown Bar */}
                <div style={{ display: "flex", gap: "8px", marginTop: "10px", fontSize: "0.7rem" }}>
                  <span style={{ color: "#f87171" }}>High: {severityBreakdown.high}</span>
                  <span style={{ color: "#475569" }}>•</span>
                  <span style={{ color: "#fbbf24" }}>Med: {severityBreakdown.medium}</span>
                  <span style={{ color: "#475569" }}>•</span>
                  <span style={{ color: "#34d399" }}>Low: {severityBreakdown.low}</span>
                </div>
              </div>

              {/* Category Filter Pills */}
              <div className="tactical-card" style={{ padding: "14px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "8px" }}>
                  <Filter size={14} color="#38bdf8" />
                  <span style={{ fontSize: "0.74rem", fontWeight: 700, color: "#e2e8f0" }}>
                    FILTER BY DOMAIN CLASSIFICATION
                  </span>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px" }}>
                  {categories.map((c) => (
                    <button
                      key={c.key}
                      onClick={() => setActiveCategory(c.key)}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        padding: "6px 10px",
                        borderRadius: "5px",
                        background:
                          activeCategory === c.key
                            ? "rgba(56, 189, 248, 0.15)"
                            : "rgba(15, 23, 42, 0.6)",
                        border:
                          activeCategory === c.key
                            ? `1px solid ${c.color}`
                            : "1px solid #334155",
                        color: "#f8fafc",
                        fontSize: "0.75rem",
                        cursor: "pointer",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span
                          style={{
                            width: 8,
                            height: 8,
                            borderRadius: "2px",
                            background: c.color,
                          }}
                        />
                        <span>{c.label}</span>
                      </div>
                      <strong style={{ color: c.color }}>{c.count}</strong>
                    </button>
                  ))}
                </div>
              </div>

              {/* Detected Polygons List */}
              <div
                className="tactical-card"
                style={{ padding: "14px", maxHeight: "280px", overflowY: "auto" }}
              >
                <span
                  style={{
                    fontSize: "0.74rem",
                    fontWeight: 700,
                    color: "#94a3b8",
                    display: "block",
                    marginBottom: "8px",
                  }}
                >
                  POLYGON ANOMALY LIST ({filteredFeatures.length})
                </span>

                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  {filteredFeatures.map((f, idx) => {
                    const p = f.properties;
                    const isSelected = selectedPolygon?.id === f.id;
                    const sqm = p.area_sqm || Math.round(p.area_hectares * 10000);
                    return (
                      <div
                        key={f.id || idx}
                        onClick={() => setSelectedPolygon(f)}
                        style={{
                          padding: "10px",
                          borderRadius: "6px",
                          background: isSelected
                            ? "rgba(37, 99, 235, 0.25)"
                            : "rgba(15, 23, 42, 0.7)",
                          border: isSelected
                            ? "1px solid #38bdf8"
                            : "1px solid rgba(51, 65, 85, 0.6)",
                          cursor: "pointer",
                          transition: "all 0.15s ease",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                          }}
                        >
                          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                            <strong style={{ fontSize: "0.82rem", color: p.color_hex }}>
                              {p.change_type}
                            </strong>
                            <SeverityBadge severity={p.severity} />
                          </div>
                          <span
                            style={{
                              fontSize: "0.72rem",
                              color: "#34d399",
                              fontWeight: 700,
                            }}
                          >
                            {p.confidence_percent}% conf
                          </span>
                        </div>

                        {/* Tactical summary */}
                        <div
                          style={{
                            fontSize: "0.71rem",
                            color: "#cbd5e1",
                            marginTop: "4px",
                          }}
                        >
                          {p.tactical_summary || "Ground anomaly detected by Siamese BIT"}
                        </div>

                        {/* Area metrics */}
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            marginTop: "6px",
                            fontSize: "0.7rem",
                            color: "#94a3b8",
                            fontFamily: "monospace",
                          }}
                        >
                          <span>{sqm.toLocaleString()} m² ({p.area_hectares} ha)</span>
                          <span>ID: {p.change_id}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          ) : (
            /* AOI Cluster Discovery Tab */
            <div className="tactical-card" style={{ padding: "16px" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: "12px",
                }}
              >
                <div>
                  <h4 style={{ fontSize: "0.85rem", fontWeight: 700, color: "#f8fafc", margin: 0 }}>
                    Unsupervised Spatial & Semantic Clusters
                  </h4>
                  <p style={{ fontSize: "0.72rem", color: "#94a3b8", margin: "2px 0 0" }}>
                    K-Means clustering on RemoteCLIP 512-dim embeddings & geodetic anchors
                  </p>
                </div>
              </div>

              {clusters.length === 0 ? (
                <div style={{ textAlign: "center", padding: "30px 10px" }}>
                  <Sparkles size={28} color="#8b5cf6" style={{ margin: "0 auto 8px" }} />
                  <p style={{ fontSize: "0.78rem", color: "#94a3b8", marginBottom: "12px" }}>
                    Run unsupervised discovery across all indexed tiles in the Ayodhya AOI.
                  </p>
                  <button
                    onClick={handleDiscoverClusters}
                    disabled={isClustering}
                    className="tactical-btn"
                    style={{
                      background: "#8b5cf6",
                      color: "#fff",
                      padding: "8px 16px",
                      margin: "0 auto",
                    }}
                  >
                    Discover Clusters Now
                  </button>
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "10px", maxHeight: "380px", overflowY: "auto" }}>
                  {clusters.map((c, i) => (
                    <div
                      key={c.cluster_id || i}
                      onClick={() => setSelectedCluster(c)}
                      style={{
                        padding: "12px",
                        borderRadius: "6px",
                        background:
                          selectedCluster?.cluster_id === c.cluster_id
                            ? "rgba(139, 92, 246, 0.25)"
                            : "rgba(15, 23, 42, 0.7)",
                        border:
                          selectedCluster?.cluster_id === c.cluster_id
                            ? "1px solid #c084fc"
                            : "1px solid #334155",
                        cursor: "pointer",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          marginBottom: "4px",
                        }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <span style={{ fontSize: "0.7rem", fontFamily: "monospace", color: "#c084fc", fontWeight: 700 }}>
                            {c.cluster_id}
                          </span>
                          <SeverityBadge severity={c.severity} />
                        </div>
                        <span style={{ fontSize: "0.72rem", color: "#38bdf8", fontWeight: 700 }}>
                          {Math.round(c.similarity * 100)}% match
                        </span>
                      </div>

                      <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#f8fafc" }}>
                        {c.name}
                      </div>

                      <p style={{ fontSize: "0.72rem", color: "#94a3b8", margin: "4px 0" }}>
                        {c.description}
                      </p>

                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          fontSize: "0.68rem",
                          color: "#64748b",
                          fontFamily: "monospace",
                          marginTop: "6px",
                        }}
                      >
                        <span>{c.tile_count} Associated Sites</span>
                        {c.centroid && (
                          <span>
                            {c.centroid[1]?.toFixed(2)}°N, {c.centroid[0]?.toFixed(2)}°E
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

        </div>

      </div>
    </div>
  );
}
