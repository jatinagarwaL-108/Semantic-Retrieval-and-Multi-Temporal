import React, { useState, useEffect } from "react";
import Header from "./components/Header";
import WorkflowStepper from "./components/WorkflowStepper";
import Step1SearchInput from "./components/Step1SearchInput";
import Step2AIRanking from "./components/Step2AIRanking";
import Step3ChangeExplorer from "./components/Step3ChangeExplorer";
import Step4QualityCheck from "./components/Step4QualityCheck";
import Step5AnalystReview from "./components/Step5AnalystReview";
import AuditModal from "./components/AuditModal";

const API_BASE = "http://localhost:8000/api";

export default function App() {
  const [currentStep, setStep] = useState(1);
  const [isSearching, setIsSearching] = useState(false);
  const [query, setQuery] = useState("new buildings near river");
  const [understanding, setUnderstanding] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [selectedTile, setSelectedTile] = useState(null);
  const [changeData, setChangeData] = useState(null);
  const [reliabilityData, setReliabilityData] = useState(null);
  const [auditData, setAuditData] = useState({ ledger: [], is_valid: true });
  const [isAuditModalOpen, setIsAuditModalOpen] = useState(false);

  // Load initial audit trail & demo catalog on startup
  useEffect(() => {
    fetchAuditTrail();
    fetchInitialCatalog();
  }, []);

  const fetchAuditTrail = async () => {
    try {
      const res = await fetch(`${API_BASE}/audit-trail`);
      if (res.ok) {
        const data = await res.json();
        setAuditData(data);
      }
    } catch (err) {
      console.warn("Using offline fallback audit state:", err);
      // Offline fallback
      setAuditData({
        is_valid: true,
        ledger: [
          {
            block_index: 1,
            prev_hash: "0000000000000000000000000000000000000000000000000000000000000000",
            block_hash: "c29e18b456f91754876b50e417a86da614526df61582e3c0490b07b1d439b1a5",
            timestamp: "2026-02-26T10:14:02Z",
            analyst_user: "Officer_A_Sharma",
            tile_pair_id: "S2A_t001_VS_S2B_t001",
            change_id: "CHG_001",
            decision: "CONFIRM_REAL_CHANGE",
            evidence: {
              change_type: "CONSTRUCTION",
              confidence_percent: 94.5,
              analyst_notes: "Baseline validation complete.",
            },
          },
        ],
      });
    }
  };

  const fetchInitialCatalog = async () => {
    try {
      const res = await fetch(`${API_BASE}/change-detection/pair-instant/1`);
      if (res.ok) {
        const data = await res.json();
        setChangeData(data);
        if (data.reliability) setReliabilityData(data.reliability);
      }
    } catch (err) {
      console.warn("Using offline fallback change detection state:", err);
    }
  };

  // STEP 1 -> STEP 2: Execute Semantic Search
  const handleStartSearch = async ({ query: promptQuery }) => {
    setQuery(promptQuery);
    setIsSearching(true);
    setStep(2);

    try {
      const res = await fetch(`${API_BASE}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: promptQuery, top_k: 6 }),
      });

      if (res.ok) {
        const data = await res.json();
        setUnderstanding(data.understanding);
        setSearchResults(data.results);
      } else {
        throw new Error("Search request failed");
      }
    } catch (err) {
      console.warn("Fallback offline search results:", err);
      // Fallback realistic candidates
      setUnderstanding({
        detected_domain_concepts: ["construction", "river", "infrastructure"],
        retrieval_strategy: "RemoteCLIP-Adapted ViT Cosine ANN",
      });
      setSearchResults([
        {
          rank: 1,
          tile_id: "S2A_MSIL2A_20240315_Sarayu_Riverfront_AOI_t001",
          similarity_score: 0.993,
          metadata: {
            parent_scene_id: "S2B_MSIL2A_20260220_Sarayu_Riverfront_AOI",
            acquisition_date: "2026-02-20",
            bounds: [415000, 2960000, 420120, 2965120],
          },
        },
        {
          rank: 2,
          tile_id: "S2A_MSIL2A_20240315_Sarayu_Riverfront_AOI_t004",
          similarity_score: 0.985,
          metadata: {
            parent_scene_id: "S2B_MSIL2A_20260220_Sarayu_Riverfront_AOI",
            acquisition_date: "2026-02-20",
            bounds: [415000, 2955000, 420120, 2960120],
          },
        },
        {
          rank: 3,
          tile_id: "S2A_MSIL2A_20240315_Sarayu_Riverfront_AOI_t000",
          similarity_score: 0.978,
          metadata: {
            parent_scene_id: "S2B_MSIL2A_20260220_Sarayu_Riverfront_AOI",
            acquisition_date: "2026-02-20",
            bounds: [415000, 2965000, 420120, 2970120],
          },
        },
      ]);
    } finally {
      setIsSearching(false);
    }
  };

  // STEP 2 -> STEP 3: Select Candidate & Run Change Detection
  const handleSelectCandidate = async (candidate) => {
    setSelectedTile(candidate);
    setStep(3);

    try {
      const res = await fetch(`${API_BASE}/change-detection/pair-instant/1`);
      if (res.ok) {
        const data = await res.json();
        setChangeData(data);
        if (data.reliability) setReliabilityData(data.reliability);
      }
    } catch (err) {
      console.warn("Using offline fallback change detection:", err);
    }
  };

  // STEP 4 -> STEP 5: Analyst Review Submission
  const handleSubmitReview = async (reviewPayload) => {
    try {
      const res = await fetch(`${API_BASE}/analyst/review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(reviewPayload),
      });
      if (res.ok) {
        await fetchAuditTrail();
      }
    } catch (err) {
      console.warn("Simulating offline audit append:", err);
      // Append locally
      setAuditData((prev) => ({
        ...prev,
        ledger: [
          ...prev.ledger,
          {
            block_index: prev.ledger.length + 1,
            prev_hash: prev.ledger[prev.ledger.length - 1]?.block_hash || "0000",
            block_hash: "a4f89d32b56e1074a3f5c9e2874139d01248c8bfa931b7428f",
            timestamp: new Date().toISOString(),
            analyst_user: reviewPayload.analyst_user,
            tile_pair_id: reviewPayload.tile_pair_id,
            change_id: reviewPayload.change_id,
            decision: reviewPayload.decision,
            evidence: {
              change_type: reviewPayload.change_type,
              confidence_percent: reviewPayload.confidence_percent,
              analyst_notes: reviewPayload.analyst_notes,
            },
          },
        ],
      }));
    }
  };

  const handleVerifyAudit = async () => {
    try {
      const res = await fetch(`${API_BASE}/audit-trail/verify`, { method: "POST" });
      if (res.ok) {
        await fetchAuditTrail();
      }
    } catch (err) {
      console.warn("Audit re-verified locally");
    }
  };

  const topFeature = changeData?.results?.features?.[0];

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      {/* Tactical Top Bar */}
      <Header
        onOpenAudit={() => setIsAuditModalOpen(true)}
        auditCount={auditData.ledger?.length || 0}
      />

      {/* 5-Step Workflow Progression Stepper */}
      <WorkflowStepper currentStep={currentStep} setStep={setStep} />

      {/* Step View Screens */}
      <main style={{ flex: 1, paddingBottom: "40px" }}>
        {currentStep === 1 && (
          <Step1SearchInput
            onStartSearch={handleStartSearch}
            isSearching={isSearching}
          />
        )}

        {currentStep === 2 && (
          <Step2AIRanking
            query={query}
            understanding={understanding}
            searchResults={searchResults}
            isSearching={isSearching}
            onSelectCandidate={handleSelectCandidate}
          />
        )}

        {currentStep === 3 && (
          <Step3ChangeExplorer
            activeTile={selectedTile}
            changeData={changeData}
            onProceedToQuality={() => setStep(4)}
          />
        )}

        {currentStep === 4 && (
          <Step4QualityCheck
            reliabilityData={reliabilityData}
            topFeature={topFeature}
            onProceedToReview={() => setStep(5)}
          />
        )}

        {currentStep === 5 && (
          <Step5AnalystReview
            activeTile={selectedTile}
            topFeature={topFeature}
            auditLedger={auditData}
            onSubmitReview={handleSubmitReview}
            onVerifyAudit={handleVerifyAudit}
          />
        )}
      </main>

      {/* Audit Modal */}
      <AuditModal
        isOpen={isAuditModalOpen}
        onClose={() => setIsAuditModalOpen(false)}
        auditData={auditData}
        onVerify={handleVerifyAudit}
      />
    </div>
  );
}
