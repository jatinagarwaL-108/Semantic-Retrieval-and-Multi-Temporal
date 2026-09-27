import React from "react";
import { Satellite, ShieldCheck, Database, Lock, Activity, Layers } from "lucide-react";

export default function Header({ onOpenAudit, auditCount = 0 }) {
  return (
    <header style={{
      background: "linear-gradient(180deg, rgba(15, 23, 42, 0.95) 0%, rgba(11, 15, 25, 0.9) 100%)",
      borderBottom: "1px solid rgba(59, 130, 246, 0.25)",
      padding: "14px 28px",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      backdropFilter: "blur(12px)",
      position: "sticky",
      top: 0,
      zIndex: 100,
    }}>
      {/* Brand Identity */}
      <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
        <div style={{
          width: 44,
          height: 44,
          borderRadius: 10,
          background: "linear-gradient(135deg, #0ea5e9, #2563eb)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: "0 0 16px rgba(14, 165, 233, 0.4)",
        }}>
          <Satellite size={26} color="#ffffff" />
        </div>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{
              fontSize: "1.35rem",
              fontWeight: 800,
              letterSpacing: "0.08em",
              background: "linear-gradient(90deg, #f8fafc, #93c5fd)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              textTransform: "uppercase",
            }}>
              MiraeNova
            </h1>
            <span style={{
              fontSize: "0.68rem",
              fontWeight: 700,
              background: "rgba(59, 130, 246, 0.15)",
              color: "#60a5fa",
              border: "1px solid rgba(59, 130, 246, 0.35)",
              padding: "2px 8px",
              borderRadius: 4,
              letterSpacing: "0.06em",
            }}>
              SIH 2026 • PS 26227
            </span>
          </div>
          <p style={{ fontSize: "0.76rem", color: "#94a3b8", marginTop: 2 }}>
            Air-Gapped Semantic Retrieval & Multi-Temporal Sentinel-2 Change Intelligence
          </p>
        </div>
      </div>

      {/* System Status Indicators */}
      <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
        {/* Raw Band Status */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "6px",
          background: "rgba(30, 41, 59, 0.6)",
          padding: "6px 12px",
          borderRadius: 6,
          border: "1px solid rgba(100, 116, 139, 0.3)",
          fontSize: "0.75rem",
        }}>
          <Layers size={14} color="#38bdf8" />
          <span style={{ color: "#94a3b8" }}>Source:</span>
          <strong style={{ color: "#38bdf8" }}>Sentinel-2 L2A BOA</strong>
        </div>

        {/* Offline Air-Gapped Badge */}
        <div style={{
          display: "flex",
          alignItems: "center",
          gap: "6px",
          background: "rgba(16, 185, 129, 0.12)",
          padding: "6px 12px",
          borderRadius: 6,
          border: "1px solid rgba(16, 185, 129, 0.35)",
          fontSize: "0.75rem",
        }}>
          <span style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: "#10b981",
            boxShadow: "0 0 8px #10b981",
          }} className="animate-pulse-slow" />
          <span style={{ color: "#34d399", fontWeight: 600 }}>AIR-GAPPED OFFLINE</span>
        </div>

        {/* Audit Trail Button */}
        <button
          onClick={onOpenAudit}
          className="tactical-btn"
          style={{
            background: "rgba(245, 158, 11, 0.12)",
            border: "1px solid rgba(245, 158, 11, 0.4)",
            color: "#fbbf24",
            padding: "6px 14px",
            fontSize: "0.75rem",
          }}
        >
          <Lock size={14} />
          <span>Audit Ledger ({auditCount})</span>
        </button>
      </div>
    </header>
  );
}
