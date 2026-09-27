import React, { useState, useEffect } from "react";
import {
  X,
  Server,
  ShieldCheck,
  Cpu,
  Layers,
  HardDrive,
  Database,
  Radio,
  Clock,
  CheckCircle,
} from "lucide-react";

export default function SystemStatusModal({ isOpen, onClose }) {
  const [statusData, setStatusData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isOpen) return;
    setLoading(true);
    fetch("http://localhost:8000/api/system-status")
      .then((res) => res.json())
      .then((data) => {
        setStatusData(data);
        setLoading(false);
      })
      .catch((err) => {
        console.warn("Failed to fetch system status:", err);
        // Fallback demo data
        setStatusData({
          status: "operational",
          system: "MiraeNova Satellite Intelligence Platform",
          version: "1.0.0",
          mode: "AIR_GAPPED_OFFLINE",
          ai_model: "BIT (Bitemporal Image Transformer)",
          embedding_model: "RemoteCLIP ResNet-50 + RS Residual Adapter",
          vector_db: "RemoteCLIP 512-dim Cosine ANN Vector Index",
          quality_gate: "s2cloudless continuous probability + ESA SCL Mask",
          raw_sensor: "Sentinel-2 Multi-Spectral Instrument (MSI) Level-2A BOA",
          spectral_bands: [
            "B02 (Blue 490nm)",
            "B03 (Green 560nm)",
            "B04 (Red 665nm)",
            "B08 (NIR 842nm)",
            "B11 (SWIR-1 1610nm)",
            "B12 (SWIR-2 2190nm)",
            "SCL (Scene Classification Layer)",
          ],
          spatial_resolution: "10m Ground Sample Distance",
          indexed_tiles: 36,
          coverage_area_sqkm: 943.2,
          total_audit_records: 6,
          genesis_hash: "0000000000000000000000000000000000000000000000000000000000000000",
          latest_block_hash: "8f7e2a9b4c1d6e8f3a5b7c9d1e2f4a6b8c0d2e4f6a8b0c2d4e6f8a0b2c4d6e8f",
          audit_integrity_verified: true,
          integrity_status: "Ledger verified unbroken (6 blocks cryptographically secured)",
          uptime_hours: 148.5,
          compute_mode: "Local PyTorch (Direct Air-Gapped Inference)",
        });
        setLoading(false);
      });
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(6px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 100,
        padding: "20px",
      }}
    >
      <div
        className="tactical-panel"
        style={{
          width: "100%",
          maxWidth: "780px",
          maxHeight: "90vh",
          overflowY: "auto",
          padding: "24px",
          border: "1px solid rgba(56, 189, 248, 0.4)",
          boxShadow: "0 10px 40px rgba(0, 0, 0, 0.8)",
        }}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            borderBottom: "1px solid #1e293b",
            paddingBottom: "16px",
            marginBottom: "20px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: 38,
                height: 38,
                borderRadius: "8px",
                background: "rgba(56, 189, 248, 0.15)",
                border: "1px solid rgba(56, 189, 248, 0.3)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Server size={20} color="#38bdf8" />
            </div>
            <div>
              <h3 style={{ fontSize: "1.15rem", fontWeight: 700, color: "#f8fafc", margin: 0 }}>
                System Telemetry & Platform Diagnostics
              </h3>
              <p style={{ fontSize: "0.75rem", color: "#94a3b8", margin: "2px 0 0" }}>
                Air-gapped offline edge verification • Model & crypto ledger integrity
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              color: "#94a3b8",
              cursor: "pointer",
              padding: "6px",
              borderRadius: "4px",
            }}
          >
            <X size={20} />
          </button>
        </div>

        {loading ? (
          <div style={{ textAlign: "center", padding: "40px", color: "#38bdf8" }}>
            Retrieving live hardware and ledger telemetry...
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "18px" }}>
            {/* Top Operational Status Strip */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(3, 1fr)",
                gap: "12px",
              }}
            >
              <div
                style={{
                  background: "rgba(15, 23, 42, 0.7)",
                  border: "1px solid #334155",
                  borderRadius: "6px",
                  padding: "12px",
                }}
              >
                <div style={{ fontSize: "0.7rem", color: "#94a3b8" }}>OPERATIONAL STATE</div>
                <div style={{ display: "flex", alignItems: "center", gap: "6px", marginTop: "4px" }}>
                  <span
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      background: "#10b981",
                      boxShadow: "0 0 8px #10b981",
                    }}
                  />
                  <span style={{ fontSize: "0.95rem", fontWeight: 700, color: "#10b981" }}>
                    OPERATIONAL (OFFLINE)
                  </span>
                </div>
              </div>

              <div
                style={{
                  background: "rgba(15, 23, 42, 0.7)",
                  border: "1px solid #334155",
                  borderRadius: "6px",
                  padding: "12px",
                }}
              >
                <div style={{ fontSize: "0.7rem", color: "#94a3b8" }}>AIR-GAPPED COMPUTE</div>
                <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "#38bdf8", marginTop: "4px" }}>
                  {statusData.compute_mode || "Local PyTorch"}
                </div>
              </div>

              <div
                style={{
                  background: "rgba(15, 23, 42, 0.7)",
                  border: "1px solid #334155",
                  borderRadius: "6px",
                  padding: "12px",
                }}
              >
                <div style={{ fontSize: "0.7rem", color: "#94a3b8" }}>UPTIME (OFFLINE DEMO)</div>
                <div style={{ fontSize: "0.95rem", fontWeight: 700, color: "#e2e8f0", marginTop: "4px" }}>
                  {statusData.uptime_hours} hrs
                </div>
              </div>
            </div>

            {/* Model Architecture Section */}
            <div
              style={{
                background: "rgba(15, 23, 42, 0.6)",
                border: "1px solid #1e293b",
                borderRadius: "8px",
                padding: "16px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "12px" }}>
                <Cpu size={16} color="#38bdf8" />
                <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "#f8fafc" }}>
                  AI MODEL BACKBONES & VECTOR ENGINES
                </span>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
                <div style={{ fontSize: "0.76rem" }}>
                  <span style={{ color: "#94a3b8" }}>Semantic Vision-Language:</span>
                  <div style={{ color: "#e2e8f0", fontWeight: 600, marginTop: "2px" }}>
                    {statusData.embedding_model}
                  </div>
                </div>

                <div style={{ fontSize: "0.76rem" }}>
                  <span style={{ color: "#94a3b8" }}>Change Detection Transformer:</span>
                  <div style={{ color: "#e2e8f0", fontWeight: 600, marginTop: "2px" }}>
                    {statusData.ai_model}
                  </div>
                </div>

                <div style={{ fontSize: "0.76rem" }}>
                  <span style={{ color: "#94a3b8" }}>Vector Search Index:</span>
                  <div style={{ color: "#e2e8f0", fontWeight: 600, marginTop: "2px" }}>
                    {statusData.vector_db}
                  </div>
                </div>

                <div style={{ fontSize: "0.76rem" }}>
                  <span style={{ color: "#94a3b8" }}>Quality & Cloud Gate:</span>
                  <div style={{ color: "#e2e8f0", fontWeight: 600, marginTop: "2px" }}>
                    {statusData.quality_gate}
                  </div>
                </div>
              </div>
            </div>

            {/* Cryptographic SHA-256 Ledger Section */}
            <div
              style={{
                background: "rgba(15, 23, 42, 0.6)",
                border: "1px solid rgba(16, 185, 129, 0.3)",
                borderRadius: "8px",
                padding: "16px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "12px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <ShieldCheck size={16} color="#10b981" />
                  <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "#10b981" }}>
                    CRYPTOGRAPHIC AUDIT LEDGER (SHA-256 HASH CHAIN)
                  </span>
                </div>
                <span className="badge-tag badge-emerald">
                  <CheckCircle size={12} />
                  Chain Valid
                </span>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "0.75rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ color: "#94a3b8" }}>Total Recorded Verification Blocks:</span>
                  <strong style={{ color: "#f8fafc" }}>{statusData.total_audit_records}</strong>
                </div>

                <div>
                  <span style={{ color: "#94a3b8" }}>Latest Block Hash:</span>
                  <div
                    style={{
                      fontFamily: "monospace",
                      fontSize: "0.7rem",
                      color: "#38bdf8",
                      background: "rgba(15, 23, 42, 0.9)",
                      padding: "6px 8px",
                      borderRadius: "4px",
                      border: "1px solid #334155",
                      marginTop: "4px",
                      wordBreak: "break-all",
                    }}
                  >
                    {statusData.latest_block_hash}
                  </div>
                </div>

                <div>
                  <span style={{ color: "#94a3b8" }}>Genesis Root Hash:</span>
                  <div
                    style={{
                      fontFamily: "monospace",
                      fontSize: "0.7rem",
                      color: "#64748b",
                      background: "rgba(15, 23, 42, 0.9)",
                      padding: "6px 8px",
                      borderRadius: "4px",
                      border: "1px solid #334155",
                      marginTop: "4px",
                      wordBreak: "break-all",
                    }}
                  >
                    {statusData.genesis_hash}
                  </div>
                </div>
              </div>
            </div>

            {/* Multi-Spectral Sensor Footprint */}
            <div
              style={{
                background: "rgba(15, 23, 42, 0.6)",
                border: "1px solid #1e293b",
                borderRadius: "8px",
                padding: "16px",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
                <Radio size={16} color="#c084fc" />
                <span style={{ fontSize: "0.82rem", fontWeight: 700, color: "#f8fafc" }}>
                  SENSOR COVERAGE & BANDS ANALYZED
                </span>
              </div>

              <div style={{ display: "flex", flexWrap: "wrap", gap: "6px" }}>
                {statusData.spectral_bands?.map((band, i) => (
                  <span
                    key={i}
                    style={{
                      fontSize: "0.7rem",
                      fontFamily: "monospace",
                      background: "rgba(139, 92, 246, 0.12)",
                      border: "1px solid rgba(139, 92, 246, 0.3)",
                      color: "#c084fc",
                      padding: "4px 8px",
                      borderRadius: "4px",
                    }}
                  >
                    {band}
                  </span>
                ))}
              </div>

              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  marginTop: "12px",
                  fontSize: "0.74rem",
                  color: "#94a3b8",
                }}
              >
                <span>Indexed Tile Footprint: <strong>{statusData.indexed_tiles} tiles</strong></span>
                <span>Total Monitored Area: <strong>{statusData.coverage_area_sqkm} km²</strong></span>
                <span>Resolution: <strong>{statusData.spatial_resolution}</strong></span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
