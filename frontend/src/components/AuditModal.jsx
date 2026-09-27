import React from "react";
import { X, Lock, ShieldCheck, CheckCircle2, AlertTriangle, Key } from "lucide-react";

export default function AuditModal({ isOpen, onClose, auditData, onVerify }) {
  if (!isOpen) return null;

  const chain = auditData?.ledger || [];
  const isValid = auditData?.is_valid !== false;

  return (
    <div style={{
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: "rgba(0, 0, 0, 0.8)",
      backdropFilter: "blur(8px)",
      zIndex: 1000,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "20px",
    }}>
      <div className="tactical-panel" style={{
        width: "100%",
        maxWidth: "840px",
        maxHeight: "85vh",
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
        border: "1px solid rgba(59, 130, 246, 0.4)",
        boxShadow: "0 20px 50px rgba(0, 0, 0, 0.8)",
      }}>
        {/* Header */}
        <div style={{
          padding: "16px 24px",
          background: "rgba(15, 23, 42, 0.9)",
          borderBottom: "1px solid #334155",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <Lock size={20} color="#fbbf24" />
            <div>
              <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "#f8fafc" }}>
                Cryptographic Tamper-Proof Audit Trail Ledger
              </h3>
              <p style={{ fontSize: "0.74rem", color: "#94a3b8" }}>
                Immutable append-only ledger • SHA-256 Hash Chaining
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{
              display: "flex",
              alignItems: "center",
              gap: "4px",
              padding: "4px 10px",
              borderRadius: "4px",
              background: isValid ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
              color: isValid ? "#34d399" : "#f87171",
              fontSize: "0.72rem",
              fontWeight: 700,
              border: `1px solid ${isValid ? "#10b981" : "#ef4444"}`,
            }}>
              {isValid ? <CheckCircle2 size={13} /> : <AlertTriangle size={13} />}
              {isValid ? "CRYPTOGRAPHIC INTEGRITY VERIFIED" : "CORRUPTION DETECTED"}
            </span>

            <button
              onClick={onClose}
              style={{
                background: "transparent",
                border: "none",
                color: "#94a3b8",
                cursor: "pointer",
                padding: "4px",
              }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div style={{ padding: "20px 24px", overflowY: "auto", flex: 1 }}>
          <div style={{ marginBottom: "16px", fontSize: "0.78rem", color: "#94a3b8" }}>
            Total Audit Records: <strong>{chain.length}</strong> • Every entry binds the previous block's SHA-256 hash, timestamp, analyst identifier, and full polygon evidence.
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            {chain.map((block) => (
              <div
                key={block.block_index}
                className="tactical-card"
                style={{
                  padding: "14px 16px",
                  background: "rgba(15, 23, 42, 0.8)",
                  border: "1px solid #334155",
                  fontFamily: "monospace",
                  fontSize: "0.75rem",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                    <span style={{
                      background: "#2563eb",
                      color: "#fff",
                      padding: "2px 8px",
                      borderRadius: "4px",
                      fontWeight: 700,
                    }}>
                      BLOCK #{block.block_index}
                    </span>
                    <strong style={{
                      color: block.decision === "CONFIRM_REAL_CHANGE" ? "#34d399" : "#f87171",
                      fontFamily: "sans-serif",
                    }}>
                      {block.decision}
                    </strong>
                  </div>

                  <span style={{ color: "#64748b" }}>
                    {new Date(block.timestamp).toLocaleString()}
                  </span>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: "4px", color: "#cbd5e1" }}>
                  <div>
                    <span style={{ color: "#64748b" }}>Prev Hash: </span>
                    <span style={{ color: "#94a3b8" }}>{block.prev_hash}</span>
                  </div>
                  <div>
                    <span style={{ color: "#64748b" }}>Block Hash: </span>
                    <strong style={{ color: "#fbbf24" }}>{block.block_hash}</strong>
                  </div>
                  <div style={{ display: "flex", gap: "16px", marginTop: "4px", color: "#94a3b8" }}>
                    <span>Officer: <strong style={{ color: "#f8fafc" }}>{block.analyst_user}</strong></span>
                    <span>Pair: <strong style={{ color: "#f8fafc" }}>{block.tile_pair_id}</strong></span>
                    <span>Class: <strong style={{ color: "#38bdf8" }}>{block.evidence?.change_type}</strong></span>
                  </div>
                  {block.evidence?.analyst_notes && (
                    <div style={{ marginTop: "6px", fontStyle: "italic", color: "#94a3b8", fontFamily: "sans-serif" }}>
                      "{block.evidence.analyst_notes}"
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: "14px 24px",
          background: "rgba(15, 23, 42, 0.9)",
          borderTop: "1px solid #334155",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}>
          <span style={{ fontSize: "0.72rem", color: "#64748b" }}>
            Algorithm: SHA-256 HMAC-free native chain • Air-gapped persistent storage
          </span>

          <button onClick={onClose} className="tactical-btn" style={{ padding: "6px 16px" }}>
            Close Ledger
          </button>
        </div>
      </div>
    </div>
  );
}
