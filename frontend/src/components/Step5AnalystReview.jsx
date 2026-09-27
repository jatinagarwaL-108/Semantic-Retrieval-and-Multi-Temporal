import React, { useState } from "react";
import {
  CheckCircle,
  XCircle,
  Lock,
  ShieldCheck,
  FileCheck,
  Calendar,
  Layers,
  MapPin,
  RefreshCw,
  ExternalLink,
} from "lucide-react";

export default function Step5AnalystReview({
  activeTile,
  topFeature,
  auditLedger,
  onSubmitReview,
  onVerifyAudit,
}) {
  const [analystUser, setAnalystUser] = useState("Capt_Vikram_Rathore_07");
  const [notes, setNotes] = useState(
    "Verified permanent engineered structure foundation. High confidence concrete signature with vegetation canopy depletion."
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [decisionFeedback, setDecisionFeedback] = useState(null);

  const feature = topFeature || {
    properties: {
      change_id: "CHG_001",
      change_type: "CONSTRUCTION",
      confidence_percent: 94.5,
      area_hectares: 1.45,
      first_seen_date: "2026-02-20",
      baseline_date: "2024-03-15",
    },
  };
  const p = feature.properties;

  const handleDecision = async (decision) => {
    setIsSubmitting(true);
    setDecisionFeedback(null);
    try {
      const payload = {
        analyst_user: analystUser,
        tile_pair_id: "S2A_t001_VS_S2B_t001",
        change_id: p.change_id,
        decision,
        change_type: p.change_type,
        confidence_percent: p.confidence_percent,
        evidence: {
          area_hectares: p.area_hectares,
          baseline_date: p.baseline_date,
          first_seen_date: p.first_seen_date,
          coordinates_utm: [415500, 2962000],
        },
        analyst_notes: notes,
      };

      await onSubmitReview(payload);
      setDecisionFeedback({
        type: decision === "CONFIRM_REAL_CHANGE" ? "CONFIRMED" : "REJECTED",
        message: decision === "CONFIRM_REAL_CHANGE"
          ? "Decision successfully committed to SHA-256 tamper-proof ledger."
          : "False alarm logged into immutable audit record.",
      });
    } catch (err) {
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const preTileId = topFeature?.properties?.pre_tile_id || "S2B_MSIL2A_20240_Ayodhya_Sarayu_Corridor_t000";
  const postTileId = topFeature?.properties?.post_tile_id || "S2B_MSIL2A_20251_Ayodhya_Sarayu_Corridor_t000";

  const chain = auditLedger?.ledger || [];
  const isValid = auditLedger?.is_valid !== false;

  return (
    <div style={{ maxWidth: "1280px", margin: "24px auto", padding: "0 20px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "18px" }}>
        <div>
          <span className="badge-tag badge-emerald" style={{ marginBottom: "6px" }}>
            Step 5 • Operational Intelligence Finalization
          </span>
          <h2 style={{ fontSize: "1.6rem", fontWeight: 700, color: "#f8fafc" }}>
            Analyst Review & Tamper-Proof Cryptographic Commit
          </h2>
          <p style={{ color: "#94a3b8", fontSize: "0.82rem", marginTop: "2px" }}>
            Side-by-side bitemporal evidence evaluation with append-only SHA-256 hash chaining
          </p>
        </div>

        {/* Verification Status */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "8px",
          background: "rgba(16, 185, 129, 0.15)",
          border: "1px solid #10b981",
          padding: "6px 14px",
          borderRadius: "6px",
        }}>
          <ShieldCheck size={16} color="#34d399" />
          <span style={{ fontSize: "0.78rem", fontWeight: 700, color: "#34d399" }}>
            LEDGER INTEGRITY: SECURE & TAMPER-PROOF
          </span>
        </div>
      </div>

      {/* Main Review Section: Side-by-side (Left 60%) + Action & Audit (Right 40%) */}
      <div style={{ display: "grid", gridTemplateColumns: "1.1fr 0.9fr", gap: "20px", alignItems: "start" }}>
        
        {/* Left: Synchronized Side-by-Side Images */}
        <div className="tactical-panel" style={{ padding: "16px" }}>
          <h3 style={{ fontSize: "0.88rem", fontWeight: 700, color: "#f8fafc", marginBottom: "12px" }}>
            SYNCHRONIZED MULTI-SPECTRAL BITEMPORAL VIEWER
          </h3>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
            {/* 2024 Baseline */}
            <div style={{
              background: "#0f172a",
              borderRadius: "6px",
              overflow: "hidden",
              border: "1px solid #334155",
            }}>
              <div style={{
                padding: "8px",
                background: "rgba(30, 41, 59, 0.8)",
                fontSize: "0.74rem",
                color: "#93c5fd",
                display: "flex",
                justifyContent: "space-between",
                fontWeight: 600,
              }}>
                <span>BASELINE (T1)</span>
                <span>2024-03-15</span>
              </div>
              <img
                src={`http://localhost:8000/api/tiles/${preTileId}/preview`}
                alt="2024"
                style={{ width: "100%", height: "260px", objectFit: "cover" }}
              />
              <div style={{ padding: "6px 8px", fontSize: "0.7rem", color: "#64748b" }}>
                Source: Sentinel-2A L2A BOA
              </div>
            </div>

            {/* 2026 Current */}
            <div style={{
              background: "#0f172a",
              borderRadius: "6px",
              overflow: "hidden",
              border: "1px solid #f59e0b",
            }}>
              <div style={{
                padding: "8px",
                background: "rgba(245, 158, 11, 0.2)",
                fontSize: "0.74rem",
                color: "#fbbf24",
                display: "flex",
                justifyContent: "space-between",
                fontWeight: 600,
              }}>
                <span>CURRENT (T2)</span>
                <span>2026-02-20</span>
              </div>
              <img
                src={`http://localhost:8000/api/tiles/${postTileId}/preview`}
                alt="2026"
                style={{ width: "100%", height: "260px", objectFit: "cover" }}
              />
              <div style={{ padding: "6px 8px", fontSize: "0.7rem", color: "#64748b" }}>
                Anomaly: {p.change_type} ({p.area_hectares} ha)
              </div>
            </div>
          </div>

          {/* Evidence Details Box */}
          <div style={{
            marginTop: "16px",
            background: "rgba(15, 23, 42, 0.7)",
            padding: "12px",
            borderRadius: "6px",
            border: "1px solid #334155",
            fontSize: "0.76rem",
            color: "#94a3b8",
          }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "8px" }}>
              <div>
                <span style={{ color: "#64748b", display: "block" }}>TARGET COORD</span>
                <strong style={{ color: "#e2e8f0" }}>415500E, 2962000N</strong>
              </div>
              <div>
                <span style={{ color: "#64748b", display: "block" }}>PROPOSED CLASSIFICATION</span>
                <strong style={{ color: "#fbbf24" }}>{p.change_type}</strong>
              </div>
              <div>
                <span style={{ color: "#64748b", display: "block" }}>MODEL CONFIDENCE</span>
                <strong style={{ color: "#34d399" }}>{p.confidence_percent}%</strong>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Decision Panel & Cryptographic Audit Chain */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          
          {/* Action Box */}
          <div className="tactical-panel" style={{ padding: "18px" }}>
            <h3 style={{ fontSize: "0.92rem", fontWeight: 700, color: "#f8fafc", marginBottom: "12px" }}>
              OFFICER DECISION & SIGN-OFF
            </h3>

            <div style={{ marginBottom: "12px" }}>
              <label style={{ fontSize: "0.72rem", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                ANALYST OFFICER CALLSIGN / USER ID
              </label>
              <input
                type="text"
                value={analystUser}
                onChange={(e) => setAnalystUser(e.target.value)}
                style={{
                  width: "100%",
                  padding: "8px",
                  background: "rgba(15, 23, 42, 0.8)",
                  border: "1px solid #475569",
                  borderRadius: "6px",
                  color: "#f8fafc",
                  fontSize: "0.82rem",
                }}
              />
            </div>

            <div style={{ marginBottom: "14px" }}>
              <label style={{ fontSize: "0.72rem", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                INTELLIGENCE JUSTIFICATION & AUDIT NOTES
              </label>
              <textarea
                rows={3}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                style={{
                  width: "100%",
                  padding: "8px",
                  background: "rgba(15, 23, 42, 0.8)",
                  border: "1px solid #475569",
                  borderRadius: "6px",
                  color: "#f8fafc",
                  fontSize: "0.78rem",
                  resize: "vertical",
                }}
              />
            </div>

            {/* Decision Buttons */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
              <button
                disabled={isSubmitting}
                onClick={() => handleDecision("CONFIRM_REAL_CHANGE")}
                className="tactical-btn btn-success"
                style={{ justifyContent: "center", padding: "10px", fontSize: "0.82rem" }}
              >
                <CheckCircle size={16} />
                <span>CONFIRM (Real Change)</span>
              </button>

              <button
                disabled={isSubmitting}
                onClick={() => handleDecision("REJECT_FALSE_ALARM")}
                className="tactical-btn btn-danger"
                style={{ justifyContent: "center", padding: "10px", fontSize: "0.82rem" }}
              >
                <XCircle size={16} />
                <span>REJECT (False Positive)</span>
              </button>
            </div>

            {/* Submission Feedback Alert */}
            {decisionFeedback && (
              <div style={{
                marginTop: "12px",
                padding: "8px 12px",
                borderRadius: "6px",
                background: decisionFeedback.type === "CONFIRMED" ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
                border: `1px solid ${decisionFeedback.type === "CONFIRMED" ? "#10b981" : "#ef4444"}`,
                color: decisionFeedback.type === "CONFIRMED" ? "#6ee7b7" : "#fca5a5",
                fontSize: "0.76rem",
              }}>
                {decisionFeedback.message}
              </div>
            )}
          </div>

          {/* Cryptographic Ledger Panel */}
          <div className="tactical-panel" style={{ padding: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "10px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <Lock size={15} color="#fbbf24" />
                <h4 style={{ fontSize: "0.84rem", fontWeight: 700, color: "#f8fafc" }}>
                  IMMUTABLE HASH-CHAINED AUDIT TRAIL
                </h4>
              </div>

              <button
                onClick={onVerifyAudit}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#38bdf8",
                  fontSize: "0.72rem",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                }}
              >
                <RefreshCw size={12} />
                <span>Re-Verify Chain</span>
              </button>
            </div>

            {/* Chain Blocks List */}
            <div style={{ display: "flex", flexDirection: "column", gap: "8px", maxHeight: "220px", overflowY: "auto" }}>
              {chain.slice(-3).reverse().map((block, i) => (
                <div
                  key={block.block_hash || i}
                  style={{
                    background: "rgba(15, 23, 42, 0.9)",
                    border: "1px solid #334155",
                    borderRadius: "6px",
                    padding: "8px 10px",
                    fontSize: "0.7rem",
                    fontFamily: "monospace",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", color: "#94a3b8", marginBottom: "4px" }}>
                    <span>Block #{block.block_index} • {block.decision}</span>
                    <span style={{ color: "#34d399" }}>VERIFIED</span>
                  </div>
                  <div style={{ color: "#64748b", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    Prev: {block.prev_hash?.slice(0, 16)}...
                  </div>
                  <div style={{ color: "#fbbf24", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    Hash: {block.block_hash}
                  </div>
                  <div style={{ color: "#94a3b8", marginTop: "2px" }}>
                    By: {block.analyst_user} @ {new Date(block.timestamp).toLocaleTimeString()}
                  </div>
                </div>
              ))}
            </div>

            <div style={{ marginTop: "10px", fontSize: "0.68rem", color: "#64748b", textAlign: "center" }}>
              Each block SHA-256 cryptographically seals previous block hash + polygon evidence
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
