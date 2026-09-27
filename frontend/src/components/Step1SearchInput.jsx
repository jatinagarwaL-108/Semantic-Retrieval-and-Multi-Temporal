import React, { useState } from "react";
import { Search, MapPin, Calendar, Layers, ArrowRight, Compass, Crosshair, Check } from "lucide-react";

export default function Step1SearchInput({ onStartSearch, isSearching }) {
  const [query, setQuery] = useState("new buildings near river");
  const [selectedAOI, setSelectedAOI] = useState("Sarayu_Riverfront_AOI");
  const [startDate, setStartDate] = useState("2024-03-15");
  const [endDate, setEndDate] = useState("2026-02-20");
  const [sensor, setSensor] = useState("SENTINEL_2_L2A");

  const queryPresets = [
    "new buildings near river",
    "new bridge and expressway construction",
    "bunker-like facility structure",
    "cleared land and vegetation loss",
    "water body and riverbank alteration",
  ];

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!query.trim()) return;
    onStartSearch({ query, selectedAOI, startDate, endDate, sensor });
  };

  return (
    <div style={{ maxWidth: "1080px", margin: "32px auto", padding: "0 20px" }}>
      {/* Step Header */}
      <div style={{ marginBottom: "28px", textAlign: "center" }}>
        <span className="badge-tag badge-cyan" style={{ marginBottom: "8px" }}>
          Step 1 • Geospatial Targeting
        </span>
        <h2 style={{ fontSize: "1.8rem", fontWeight: 700, color: "#f8fafc", marginTop: "4px" }}>
          Semantic Query & Area of Interest Specification
        </h2>
        <p style={{ color: "#94a3b8", fontSize: "0.92rem", maxWidth: "680px", margin: "8px auto 0" }}>
          Enter free-text intelligence queries to retrieve multi-temporal Sentinel-2 imagery
          via RemoteCLIP cross-modal embeddings without manual spectral thresholding.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="tactical-panel" style={{ padding: "32px" }}>
        {/* Natural Language Search Input */}
        <div style={{ marginBottom: "24px" }}>
          <label style={{
            display: "block",
            fontSize: "0.85rem",
            fontWeight: 600,
            color: "#e2e8f0",
            marginBottom: "8px",
            letterSpacing: "0.03em",
          }}>
            NATURAL LANGUAGE INTELLIGENCE PROMPT
          </label>
          <div style={{
            position: "relative",
            display: "flex",
            alignItems: "center",
          }}>
            <Search
              size={20}
              color="#38bdf8"
              style={{ position: "absolute", left: "16px", pointerEvents: "none" }}
            />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. new buildings near river, new road, cleared land..."
              style={{
                width: "100%",
                padding: "16px 16px 16px 48px",
                background: "rgba(15, 23, 42, 0.9)",
                border: "1px solid rgba(59, 130, 246, 0.4)",
                borderRadius: "8px",
                color: "#f8fafc",
                fontSize: "1.05rem",
                outline: "none",
                boxShadow: "inset 0 2px 4px rgba(0,0,0,0.4)",
              }}
            />
            <button
              type="submit"
              disabled={isSearching}
              className="tactical-btn btn-primary"
              style={{
                position: "absolute",
                right: "8px",
                padding: "10px 20px",
                fontSize: "0.9rem",
              }}
            >
              <span>{isSearching ? "Searching..." : "Execute Search"}</span>
              <ArrowRight size={16} />
            </button>
          </div>

          {/* Preset Prompts */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "12px", flexWrap: "wrap" }}>
            <span style={{ fontSize: "0.75rem", color: "#64748b" }}>Suggested Queries:</span>
            {queryPresets.map((preset) => (
              <button
                key={preset}
                type="button"
                onClick={() => setQuery(preset)}
                style={{
                  background: query === preset ? "rgba(59, 130, 246, 0.25)" : "rgba(30, 41, 59, 0.6)",
                  border: query === preset ? "1px solid #3b82f6" : "1px solid #334155",
                  color: query === preset ? "#93c5fd" : "#cbd5e1",
                  fontSize: "0.75rem",
                  padding: "4px 10px",
                  borderRadius: "4px",
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                }}
              >
                {preset}
              </button>
            ))}
          </div>
        </div>

        {/* Targeting Grid */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "20px",
          marginTop: "24px",
          paddingTop: "24px",
          borderTop: "1px solid rgba(51, 65, 85, 0.5)",
        }}>
          {/* AOI Selector */}
          <div className="tactical-card" style={{ padding: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
              <MapPin size={18} color="#f59e0b" />
              <h3 style={{ fontSize: "0.88rem", fontWeight: 700, color: "#f8fafc" }}>
                TARGET AREA OF INTEREST (AOI)
              </h3>
            </div>
            <select
              value={selectedAOI}
              onChange={(e) => setSelectedAOI(e.target.value)}
              style={{
                width: "100%",
                padding: "10px",
                background: "rgba(15, 23, 42, 0.8)",
                border: "1px solid #475569",
                borderRadius: "6px",
                color: "#e2e8f0",
                fontSize: "0.85rem",
                outline: "none",
              }}
            >
              <option value="Sarayu_Riverfront_AOI">Sarayu Riverfront Sector (415000E, 2960000N - UTM 44N)</option>
              <option value="NCR_Delhi_Border_AOI">Delhi NCR Border Corridor (Demo Bitemporal)</option>
              <option value="Visakhapatnam_Port_AOI">Eastern Naval Littoral Zone (Demo Stack)</option>
            </select>
            <div style={{ marginTop: "10px", fontSize: "0.74rem", color: "#94a3b8" }}>
              Bounds: [415000, 2955000, 425000, 2965000] • 9 Tiled Sub-grids (512x512)
            </div>
          </div>

          {/* Timeframe Selector */}
          <div className="tactical-card" style={{ padding: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
              <Calendar size={18} color="#10b981" />
              <h3 style={{ fontSize: "0.88rem", fontWeight: 700, color: "#f8fafc" }}>
                MULTI-TEMPORAL WINDOW
              </h3>
            </div>
            <div style={{ display: "flex", gap: "10px" }}>
              <div style={{ flex: 1 }}>
                <span style={{ fontSize: "0.72rem", color: "#64748b", display: "block" }}>T1 (Baseline):</span>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px",
                    background: "rgba(15, 23, 42, 0.8)",
                    border: "1px solid #475569",
                    borderRadius: "6px",
                    color: "#e2e8f0",
                    fontSize: "0.82rem",
                  }}
                />
              </div>
              <div style={{ flex: 1 }}>
                <span style={{ fontSize: "0.72rem", color: "#64748b", display: "block" }}>T2 (Current):</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px",
                    background: "rgba(15, 23, 42, 0.8)",
                    border: "1px solid #475569",
                    borderRadius: "6px",
                    color: "#e2e8f0",
                    fontSize: "0.82rem",
                  }}
                />
              </div>
            </div>
            <div style={{ marginTop: "10px", fontSize: "0.74rem", color: "#94a3b8" }}>
              Temporal baseline span: 23 months (March 2024 → February 2026)
            </div>
          </div>

          {/* Sensor Choice */}
          <div className="tactical-card" style={{ padding: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
              <Layers size={18} color="#8b5cf6" />
              <h3 style={{ fontSize: "0.88rem", fontWeight: 700, color: "#f8fafc" }}>
                SATELLITE CONSTELATION
              </h3>
            </div>
            <select
              value={sensor}
              onChange={(e) => setSensor(e.target.value)}
              style={{
                width: "100%",
                padding: "10px",
                background: "rgba(15, 23, 42, 0.8)",
                border: "1px solid #475569",
                borderRadius: "6px",
                color: "#e2e8f0",
                fontSize: "0.85rem",
                outline: "none",
              }}
            >
              <option value="SENTINEL_2_L2A">Sentinel-2A/B L2A BOA (Raw Multi-Spectral COG)</option>
              <option value="LANDSAT_9_C2L2" disabled>Landsat 9 OLI-2 Surface Reflectance (Offline Archive)</option>
            </select>
            <div style={{ marginTop: "10px", fontSize: "0.74rem", color: "#94a3b8" }}>
              Bands: B02, B03, B04, B08, B11, B12 + SCL • Native Float32 BOA Reflectance
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
