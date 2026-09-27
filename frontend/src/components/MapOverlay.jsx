import React from "react";
import {
  Crosshair,
  Satellite,
  Activity,
  Compass,
  Layers,
  Sliders,
  ShieldAlert,
  Zap,
} from "lucide-react";

export default function MapOverlay({
  viewMode = "SPLIT",
  setViewMode,
  opacity = 50,
  setOpacity,
  isProcessing = false,
  detectionResult,
  selectedFeature,
  centerCoords = [82.20, 26.80],
}) {
  const features = detectionResult?.features || [];
  const totalCount = features.length;
  const highSevCount = features.filter(
    (f) => f.properties?.severity?.toLowerCase() === "high"
  ).length;

  return (
    <>
      {/* ── Top-Left HUD: Dynamic Geodetic Coordinates & Lock State ── */}
      <div
        style={{
          position: "absolute",
          top: "14px",
          left: "14px",
          zIndex: 10,
          pointerEvents: "auto",
        }}
      >
        <div
          style={{
            background: "rgba(10, 16, 28, 0.88)",
            backdropFilter: "blur(8px)",
            border: "1px solid rgba(56, 189, 248, 0.35)",
            boxShadow: "0 4px 20px rgba(0,0,0,0.6)",
            borderRadius: "6px",
            padding: "8px 12px",
            display: "flex",
            alignItems: "center",
            gap: "10px",
          }}
        >
          <Crosshair size={15} color="#38bdf8" />
          <div
            style={{
              fontFamily: "monospace",
              fontSize: "0.74rem",
              color: "#94a3b8",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <span style={{ color: "#f8fafc", fontWeight: 700 }}>
              {centerCoords[1].toFixed(4)}°N
            </span>
            <span style={{ color: "#475569" }}>|</span>
            <span style={{ color: "#f8fafc", fontWeight: 700 }}>
              {centerCoords[0].toFixed(4)}°E
            </span>
            <span style={{ color: "#475569" }}>|</span>
            <span
              style={{
                color: "#38bdf8",
                fontWeight: 700,
                letterSpacing: "0.05em",
                background: "rgba(56, 189, 248, 0.12)",
                padding: "2px 6px",
                borderRadius: "3px",
              }}
            >
              UTM-44N LOCKED
            </span>
          </div>
        </div>
      </div>

      {/* ── Top-Right HUD: Sensor & Radiometric Pipeline ── */}
      <div
        style={{
          position: "absolute",
          top: "14px",
          right: "14px",
          zIndex: 10,
          pointerEvents: "auto",
        }}
      >
        <div
          style={{
            background: "rgba(10, 16, 28, 0.88)",
            backdropFilter: "blur(8px)",
            border: "1px solid rgba(139, 92, 246, 0.35)",
            boxShadow: "0 4px 20px rgba(0,0,0,0.6)",
            borderRadius: "6px",
            padding: "8px 12px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            fontSize: "0.74rem",
            fontFamily: "monospace",
          }}
        >
          <Satellite size={15} color="#c084fc" />
          <div>
            <span style={{ color: "#c084fc", fontWeight: 700 }}>
              Sentinel-2 MSI
            </span>
            <span style={{ color: "#475569", margin: "0 6px" }}>·</span>
            <span style={{ color: "#cbd5e1" }}>Level-2A BOA (Float32)</span>
            <span style={{ color: "#475569", margin: "0 6px" }}>·</span>
            <span style={{ color: "#38bdf8" }}>10m/px GSD</span>
          </div>
        </div>
      </div>

      {/* ── Mode Switcher & Opacity Slider Overlay ── */}
      <div
        style={{
          position: "absolute",
          top: "60px",
          left: "14px",
          zIndex: 10,
          display: "flex",
          flexDirection: "column",
          gap: "8px",
        }}
      >
        {/* Mode Selector Buttons */}
        <div
          style={{
            background: "rgba(10, 16, 28, 0.92)",
            backdropFilter: "blur(8px)",
            border: "1px solid rgba(51, 65, 85, 0.7)",
            borderRadius: "6px",
            padding: "4px",
            display: "flex",
            gap: "4px",
          }}
        >
          <button
            onClick={() => setViewMode("SPLIT")}
            style={{
              background:
                viewMode === "SPLIT"
                  ? "#2563eb"
                  : "rgba(30, 41, 59, 0.6)",
              color: "#fff",
              border: "none",
              padding: "5px 10px",
              borderRadius: "4px",
              fontSize: "0.73rem",
              fontWeight: 600,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "5px",
            }}
          >
            <Sliders size={12} />
            Split Wipe
          </button>

          <button
            onClick={() => setViewMode("OPACITY")}
            style={{
              background:
                viewMode === "OPACITY"
                  ? "#2563eb"
                  : "rgba(30, 41, 59, 0.6)",
              color: "#fff",
              border: "none",
              padding: "5px 10px",
              borderRadius: "4px",
              fontSize: "0.73rem",
              fontWeight: 600,
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: "5px",
            }}
          >
            <Layers size={12} />
            Opacity Blend
          </button>

          <button
            onClick={() => setViewMode("CIR_INFRARED")}
            style={{
              background:
                viewMode === "CIR_INFRARED"
                  ? "#2563eb"
                  : "rgba(30, 41, 59, 0.6)",
              color: "#fff",
              border: "none",
              padding: "5px 10px",
              borderRadius: "4px",
              fontSize: "0.73rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            CIR False-Color
          </button>

          <button
            onClick={() => setViewMode("NDVI")}
            style={{
              background:
                viewMode === "NDVI"
                  ? "#2563eb"
                  : "rgba(30, 41, 59, 0.6)",
              color: "#fff",
              border: "none",
              padding: "5px 10px",
              borderRadius: "4px",
              fontSize: "0.73rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            NDVI Index
          </button>
        </div>

        {/* Continuous Opacity Fader Slider (When in OPACITY Mode) */}
        {viewMode === "OPACITY" && (
          <div
            style={{
              background: "rgba(10, 16, 28, 0.92)",
              backdropFilter: "blur(8px)",
              border: "1px solid rgba(56, 189, 248, 0.4)",
              borderRadius: "6px",
              padding: "8px 12px",
              width: "280px",
              display: "flex",
              flexDirection: "column",
              gap: "6px",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                fontSize: "0.7rem",
                fontFamily: "monospace",
                color: "#94a3b8",
              }}
            >
              <span style={{ color: "#60a5fa" }}>T1 Baseline (0%)</span>
              <span style={{ color: "#f8fafc", fontWeight: 700 }}>
                Blend: {opacity}%
              </span>
              <span style={{ color: "#f59e0b" }}>T2 Current (100%)</span>
            </div>
            <input
              type="range"
              min={0}
              max={100}
              value={opacity}
              onChange={(e) => setOpacity(Number(e.target.value))}
              style={{
                width: "100%",
                accentColor: "#38bdf8",
                cursor: "pointer",
              }}
            />
          </div>
        )}
      </div>

      {/* ── Bottom-Left HUD: Live Intelligence Detection Telemetry ── */}
      <div
        style={{
          position: "absolute",
          bottom: "14px",
          left: "14px",
          zIndex: 10,
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            background: "rgba(10, 16, 28, 0.88)",
            backdropFilter: "blur(8px)",
            border: isProcessing
              ? "1px solid rgba(59, 130, 246, 0.6)"
              : "1px solid rgba(16, 185, 129, 0.4)",
            boxShadow: "0 4px 20px rgba(0,0,0,0.6)",
            borderRadius: "6px",
            padding: "8px 14px",
            display: "flex",
            alignItems: "center",
            gap: "10px",
            fontFamily: "monospace",
            fontSize: "0.74rem",
          }}
        >
          <Activity
            size={16}
            color={isProcessing ? "#60a5fa" : "#34d399"}
            style={{
              animation: isProcessing ? "spin 2s linear infinite" : "none",
            }}
          />
          {isProcessing ? (
            <span style={{ color: "#93c5fd", fontWeight: 700 }}>
              AI INFERENCE IN PROGRESS • BIT TRANSFORMER SCANNING...
            </span>
          ) : (
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ color: "#34d399", fontWeight: 700 }}>
                {totalCount} ANOMALIES IDENTIFIED
              </span>
              {highSevCount > 0 && (
                <span
                  style={{
                    background: "rgba(239, 68, 68, 0.2)",
                    border: "1px solid #ef4444",
                    color: "#f87171",
                    padding: "1px 6px",
                    borderRadius: "3px",
                    fontWeight: 700,
                    fontSize: "0.68rem",
                  }}
                >
                  {highSevCount} HIGH SEVERITY
                </span>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Bottom-Right HUD: Scale Bar & Geodetic Bearing ── */}
      <div
        style={{
          position: "absolute",
          bottom: "14px",
          right: "14px",
          zIndex: 10,
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            background: "rgba(10, 16, 28, 0.88)",
            backdropFilter: "blur(8px)",
            border: "1px solid rgba(51, 65, 85, 0.7)",
            boxShadow: "0 4px 20px rgba(0,0,0,0.6)",
            borderRadius: "6px",
            padding: "8px 12px",
            display: "flex",
            alignItems: "center",
            gap: "12px",
            fontFamily: "monospace",
            fontSize: "0.72rem",
            color: "#94a3b8",
          }}
        >
          {/* Compass */}
          <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            <Compass size={14} color="#38bdf8" />
            <span style={{ color: "#f8fafc", fontWeight: 700 }}>N 0.0°</span>
          </div>

          <span style={{ color: "#475569" }}>|</span>

          {/* Scale bar */}
          <div style={{ display: "flex", flexDirection: "column", gap: "2px", alignItems: "center" }}>
            <div
              style={{
                width: "60px",
                height: "3px",
                background: "#38bdf8",
                borderRadius: "2px",
                border: "1px solid rgba(255,255,255,0.4)",
              }}
            />
            <span style={{ fontSize: "0.66rem", color: "#cbd5e1" }}>500 m</span>
          </div>
        </div>
      </div>

      {/* ── Laser Scanning Animation Effect ── */}
      {isProcessing && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            overflow: "hidden",
            pointerEvents: "none",
            zIndex: 6,
          }}
        >
          <div
            style={{
              width: "100%",
              height: "2px",
              background:
                "linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.8), transparent)",
              boxShadow: "0 0 15px rgba(56, 189, 248, 0.8)",
              animation: "scanLine 2.5s ease-in-out infinite",
            }}
          />
        </div>
      )}
    </>
  );
}
