import React from "react";
import { Search, Sparkles, MapPin, CheckCircle, ShieldAlert } from "lucide-react";

export default function WorkflowStepper({ currentStep, setStep }) {
  const steps = [
    { number: 1, label: "Search & Input", icon: Search, desc: "Prompt & AOI Selector" },
    { number: 2, label: "AI Search & Ranking", icon: Sparkles, desc: "RemoteCLIP Semantic Matches" },
    { number: 3, label: "Explore & Detect Change", icon: MapPin, desc: "BIT Multi-Spectral Overlay" },
    { number: 4, label: "Quality Check & AI Result", icon: ShieldAlert, desc: "Reliability Gate & Flags" },
    { number: 5, label: "Analyst Review & Save", icon: CheckCircle, desc: "Immutable Audit Commit" },
  ];

  return (
    <nav style={{
      background: "rgba(15, 23, 42, 0.8)",
      borderBottom: "1px solid rgba(51, 65, 85, 0.6)",
      padding: "8px 24px",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: "8px", width: "100%", maxWidth: "1280px", margin: "0 auto" }}>
        {steps.map((s, idx) => {
          const isActive = currentStep === s.number;
          const isDone = currentStep > s.number;
          const Icon = s.icon;

          return (
            <React.Fragment key={s.number}>
              <div
                onClick={() => setStep(s.number)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "10px",
                  padding: "8px 14px",
                  borderRadius: "8px",
                  cursor: "pointer",
                  background: isActive
                    ? "rgba(37, 99, 235, 0.2)"
                    : isDone
                    ? "rgba(16, 185, 129, 0.08)"
                    : "transparent",
                  border: isActive
                    ? "1px solid rgba(59, 130, 246, 0.5)"
                    : isDone
                    ? "1px solid rgba(16, 185, 129, 0.3)"
                    : "1px solid transparent",
                  transition: "all 0.2s ease",
                  flex: 1,
                }}
              >
                <div style={{
                  width: 32,
                  height: 32,
                  borderRadius: "50%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: isActive
                    ? "#2563eb"
                    : isDone
                    ? "#059669"
                    : "#1e293b",
                  color: "#fff",
                  fontSize: "0.85rem",
                  fontWeight: 700,
                  boxShadow: isActive ? "0 0 10px rgba(37, 99, 235, 0.6)" : "none",
                }}>
                  {isDone ? <CheckCircle size={16} /> : s.number}
                </div>

                <div>
                  <div style={{
                    fontSize: "0.82rem",
                    fontWeight: isActive ? 700 : 500,
                    color: isActive ? "#93c5fd" : isDone ? "#6ee7b7" : "#94a3b8",
                  }}>
                    {s.label}
                  </div>
                  <div style={{ fontSize: "0.7rem", color: "#64748b", marginTop: 1 }}>
                    {s.desc}
                  </div>
                </div>
              </div>

              {idx < steps.length - 1 && (
                <div style={{
                  width: "24px",
                  height: "2px",
                  background: isDone ? "#059669" : "#334155",
                }} />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </nav>
  );
}
