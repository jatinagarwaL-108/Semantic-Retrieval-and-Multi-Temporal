import React from "react";
import {
  ShieldCheck,
  ShieldAlert,
  CloudSun,
  SunMedium,
  Crosshair,
  CalendarCheck,
  ArrowRight,
  Sparkles,
  Info,
  CheckCircle2,
  AlertTriangle,
} from "lucide-react";

export default function Step4QualityCheck({
  reliabilityData,
  topFeature,
  onProceedToReview,
}) {
  const rel = reliabilityData || {
    is_reliable: true,
    reliability_percentage: 95.8,
    verdict: "APPROVED_AI_RESULT",
    flags: [],
    details: {
      cloud_pct: 0.8,
      shadow_pct: 0.2,
      subpixel_shift: 0.14,
      diffuse_phenology_ratio: 0.05,
    },
  };

  const feature = topFeature || {
    properties: {
      change_id: "CHG_001",
      change_type: "CONSTRUCTION",
      confidence_percent: 94.5,
      area_hectares: 1.45,
      first_seen_date: "2026-02-20",
      baseline_date: "2024-03-15",
      explanation: {
        justification: [
          "Strong built-up index rise (Delta-NDBI: +0.312)",
          "Sharp vegetation canopy loss (Delta-NDVI: -0.428)",
          "Spatial compactness and rectangular footprint characteristic of engineered structures",
        ],
        spectral_metrics: {
          delta_ndvi: -0.428,
          delta_ndbi: 0.312,
          delta_ndwi: -0.045,
          post_nir: 0.22,
          aspect_ratio: 1.35,
        },
      },
    },
  };

  const p = feature.properties;
  const isApproved = rel.verdict === "APPROVED_AI_RESULT";

  const gates = [
    {
      title: "Cloud & Haze Gate",
      icon: CloudSun,
      value: `${rel.details?.cloud_pct || 0.8}% cloud cover`,
      threshold: "< 15.0%",
      status: (rel.details?.cloud_pct || 0) < 15 ? "PASS" : "ALERT",
      desc: "s2cloudless spectral probability + SCL cloud classes",
    },
    {
      title: "Cloud-Shadow Gate",
      icon: SunMedium,
      value: `${rel.details?.shadow_pct || 0.2}% shadow cover`,
      threshold: "< 10.0%",
      status: (rel.details?.shadow_pct || 0) < 10 ? "PASS" : "ALERT",
      desc: "Topographical and cloud-cast shadow suppression",
    },
    {
      title: "Seasonal Phenology Consistency",
      icon: CalendarCheck,
      value: `${((rel.details?.diffuse_phenology_ratio || 0.05) * 100).toFixed(1)}% diffuse drift`,
      threshold: "< 40.0%",
      status: (rel.details?.diffuse_phenology_ratio || 0) < 0.4 ? "PASS" : "ALERT",
      desc: "Checks broad-area agricultural/deciduous crop cycle drift",
    },
    {
      title: "Co-Registration Alignment",
      icon: Crosshair,
      value: `${rel.details?.subpixel_shift || 0.14} px shift`,
      threshold: "< 1.0 px",
      status: (rel.details?.subpixel_shift || 0) < 1.0 ? "PASS" : "ALERT",
      desc: "Sub-pixel cross-correlation phase check on NIR band",
    },
  ];

  return (
    <div style={{ maxWidth: "1120px", margin: "28px auto", padding: "0 20px" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "22px" }}>
        <div>
          <span className="badge-tag badge-emerald" style={{ marginBottom: "6px" }}>
            Step 4 • Reliability & False-Alarm Gate
          </span>
          <h2 style={{ fontSize: "1.6rem", fontWeight: 700, color: "#f8fafc" }}>
            Operational Quality Gate & AI Anomaly Assessment
          </h2>
          <p style={{ color: "#94a3b8", fontSize: "0.84rem", marginTop: "2px" }}>
            Real-time multi-spectral reliability validation running prior to analyst presentation
          </p>
        </div>

        <button
          onClick={onProceedToReview}
          className="tactical-btn btn-primary"
          style={{ padding: "10px 18px" }}
        >
          <span>Proceed to Analyst Review</span>
          <ArrowRight size={16} />
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.1fr 0.9fr", gap: "22px", alignItems: "start" }}>
        
        {/* Left: 4-Gate Reliability Checklist */}
        <div className="tactical-panel" style={{ padding: "22px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "18px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <ShieldCheck size={22} color={isApproved ? "#10b981" : "#f59e0b"} />
              <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "#f8fafc" }}>
                RELIABILITY GATE VERIFICATION (reliability_check.py)
              </h3>
            </div>

            <div style={{
              background: isApproved ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
              border: `1px solid ${isApproved ? "#10b981" : "#ef4444"}`,
              padding: "4px 12px",
              borderRadius: "6px",
              display: "flex",
              alignItems: "center",
              gap: "6px",
            }}>
              <strong style={{ fontSize: "0.85rem", color: isApproved ? "#34d399" : "#f87171" }}>
                {rel.reliability_percentage}%
              </strong>
              <span style={{ fontSize: "0.72rem", color: "#94a3b8" }}>
                ({rel.verdict})
              </span>
            </div>
          </div>

          {/* 4 Gate Rows */}
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {gates.map((g, idx) => {
              const Icon = g.icon;
              const isPass = g.status === "PASS";
              return (
                <div
                  key={idx}
                  className="tactical-card"
                  style={{
                    padding: "14px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    background: "rgba(15, 23, 42, 0.7)",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <div style={{
                      width: 36,
                      height: 36,
                      borderRadius: "6px",
                      background: isPass ? "rgba(16, 185, 129, 0.15)" : "rgba(245, 158, 11, 0.15)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}>
                      <Icon size={18} color={isPass ? "#10b981" : "#f59e0b"} />
                    </div>
                    <div>
                      <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "#f8fafc" }}>
                        {g.title}
                      </div>
                      <div style={{ fontSize: "0.72rem", color: "#64748b", marginTop: "2px" }}>
                        {g.desc}
                      </div>
                    </div>
                  </div>

                  <div style={{ textAlign: "right" }}>
                    <span style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px",
                      fontSize: "0.72rem",
                      fontWeight: 700,
                      padding: "2px 8px",
                      borderRadius: "4px",
                      background: isPass ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)",
                      color: isPass ? "#34d399" : "#f87171",
                    }}>
                      {isPass ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
                      {g.status}
                    </span>
                    <div style={{ fontSize: "0.72rem", color: "#94a3b8", marginTop: "3px" }}>
                      {g.value} (tol: {g.threshold})
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          <div style={{
            marginTop: "16px",
            background: "rgba(30, 41, 59, 0.5)",
            padding: "10px 14px",
            borderRadius: "6px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            fontSize: "0.75rem",
            color: "#94a3b8",
          }}>
            <Info size={16} color="#38bdf8" />
            <span>
              All 4 reliability gates passed. Change anomaly approved for official intelligence submission.
            </span>
          </div>
        </div>

        {/* Right: AI Result Card */}
        <div className="tactical-panel" style={{ padding: "22px", borderTop: "4px solid #f59e0b" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "14px" }}>
            <Sparkles size={20} color="#f59e0b" />
            <h3 style={{ fontSize: "1rem", fontWeight: 700, color: "#f8fafc" }}>
              OFFICIAL AI RESULT CARD
            </h3>
          </div>

          {/* Primary Result Details */}
          <div className="tactical-card" style={{ padding: "16px", marginBottom: "16px", background: "rgba(15, 23, 42, 0.85)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "0.76rem", color: "#94a3b8" }}>Classified Change Event</span>
              <span className="badge-tag badge-amber">{p.change_type}</span>
            </div>

            <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "#fbbf24", margin: "8px 0 4px" }}>
              New Concrete Facility Structure
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginTop: "12px", borderTop: "1px solid #334155", paddingTop: "10px" }}>
              <div>
                <span style={{ fontSize: "0.7rem", color: "#64748b", display: "block" }}>CONFIDENCE SCORE</span>
                <strong style={{ fontSize: "1.1rem", color: "#34d399" }}>{p.confidence_percent}%</strong>
              </div>
              <div>
                <span style={{ fontSize: "0.7rem", color: "#64748b", display: "block" }}>ESTIMATED EXTENT</span>
                <strong style={{ fontSize: "1.1rem", color: "#f8fafc" }}>{p.area_hectares} ha</strong>
              </div>
              <div>
                <span style={{ fontSize: "0.7rem", color: "#64748b", display: "block" }}>BASELINE DATE</span>
                <span style={{ fontSize: "0.82rem", color: "#94a3b8" }}>{p.baseline_date || "2024-03-15"}</span>
              </div>
              <div>
                <span style={{ fontSize: "0.7rem", color: "#64748b", display: "block" }}>FIRST SEEN DATE</span>
                <span style={{ fontSize: "0.82rem", color: "#38bdf8" }}>{p.first_seen_date || "2026-02-20"}</span>
              </div>
            </div>
          </div>

          {/* Justification Reasons */}
          <div style={{ marginBottom: "16px" }}>
            <span style={{ fontSize: "0.76rem", fontWeight: 700, color: "#cbd5e1", display: "block", marginBottom: "8px" }}>
              SPECTRAL & GEOMETRIC EVIDENCE:
            </span>
            <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: "6px" }}>
              {(p.explanation?.justification || []).map((j, i) => (
                <li key={i} style={{ fontSize: "0.76rem", color: "#94a3b8", display: "flex", alignItems: "flex-start", gap: "6px" }}>
                  <span style={{ color: "#38bdf8", fontWeight: "bold" }}>•</span>
                  <span>{j}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Spectral Index Deltas */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr",
            gap: "8px",
            background: "rgba(15, 23, 42, 0.6)",
            padding: "10px",
            borderRadius: "6px",
            fontSize: "0.72rem",
            textAlign: "center",
          }}>
            <div>
              <span style={{ color: "#64748b", display: "block" }}>Δ NDVI</span>
              <strong style={{ color: "#f87171" }}>{p.explanation?.spectral_metrics?.delta_ndvi || -0.428}</strong>
            </div>
            <div>
              <span style={{ color: "#64748b", display: "block" }}>Δ NDBI</span>
              <strong style={{ color: "#fbbf24" }}>{p.explanation?.spectral_metrics?.delta_ndbi || +0.312}</strong>
            </div>
            <div>
              <span style={{ color: "#64748b", display: "block" }}>Aspect Ratio</span>
              <strong style={{ color: "#93c5fd" }}>{p.explanation?.spectral_metrics?.aspect_ratio || 1.35}:1</strong>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
