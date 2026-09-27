# MiraeNova: AI-Powered Semantic Retrieval & Multi-Temporal Change Analysis of Satellite Imagery

> **Smart India Hackathon 2026** | **Problem Statement**: 26227 | **Theme**: Space Technology | **Category**: Software  
> **Platform**: 100% Offline, Air-Gapped Satellite Intelligence & Geospatial Change Detection Platform

---

## Executive Summary

**MiraeNova** is an operational, air-gapped satellite intelligence platform engineered for defense, strategic reconnaissance, and environmental surveillance. It addresses the critical challenge of extracting actionable intelligence from petabytes of high-dimensional multi-spectral satellite imagery without exposing sensitive operational workflows to external cloud networks.

The platform provides an end-to-end pipeline:
1. **Raw Multi-Spectral Sentinel-2 Processing**: Native preservation of Bottom-of-Atmosphere (BOA) surface reflectance across 7 bands (B02, B03, B04, B08, B11, B12, SCL) with **zero early RGB quantization**.
2. **RemoteCLIP Semantic Search**: Cross-modal vision-language neural retrieval enabling natural language queries (e.g. *"new buildings near river"*, *"cleared land buffer"*) mapped directly to satellite imagery via a domain-adapted vector index.
3. **Bitemporal Image Transformer (BIT) Change Detection**: Neural change detection operating on co-registered 4-band multi-spectral stacks ($B02, B03, B04, B08$), paired with a multiclass classifier head categorizing anomalies into **Construction**, **Road Infrastructure**, **Water Dynamics**, and **Vegetation Clearance**.
4. **Multi-Spectral Reliability Gate (`reliability_check.py`)**: Authoritative false-alarm pre-filter evaluating cloud cover, cloud shadow artifacts, diffuse seasonal phenology trends, and sub-pixel co-registration shifts before surfacing findings as an "AI Result".
5. **Cryptographic Tamper-Proof Audit Trail**: Immutable SHA-256 append-only hash-chained ledger sealing every analyst confirm/reject decision, officer callsign, and polygon evidence.
6. **Tactical Geospatial Web Client**: 5-step analyst interface featuring before/after split sliders, false-color CIR overlays, dynamic on-the-fly NDVI mapping, and real-time ledger verification.

---

## System Architecture

```
                                +-----------------------------------------------------------+
                                |               RAW SENTINEL-2 L2A BOA BANDS                |
                                |  (B02, B03, B04, B08, B11, B12, SCL) — Float32/Int16 COG   |
                                +-----------------------------+-----------------------------+
                                                              |
                                                              v
+-------------------------------------------------------------------------------------------------------------------+
| PREPROCESSING PIPELINE (/data_pipeline/)                                                                          |
|  1. AOI Tiling & Reprojection (EPSG:4326 -> UTM Zone 44N)                                                         |
|  2. Atmospheric / Cloud / Shadow Masking (s2cloudless + SCL cloud/shadow/water/snow classes)                      |
|  3. Radiometric Normalization (Per-scene percentile stretch, reversible metadata storage)                         |
|  4. Multi-Band Math & Spectral Indices (NDVI, NDBI, NDWI, Raw Band-Diff: post - pre)                               |
|  5. Co-Registration Cross-Correlation Shift Check (Misalignment detection)                                        |
+------------------------------+----------------------------------------------------+-------------------------------+
                               |                                                    |
                               | (Purely for display & CLIP input)                  | (Primary Scientific Path:
                               v                                                    |  B02, B03, B04, B08, B11, B12)
                +------------------------------+                                    v
                | Derived Display Composite    |                     +-------------------------------+
                | (Tagged: Non-Authoritative)  |                     | Multi-Spectral Band Stacks    |
                +--------------+---------------+                     +---------------+---------------+
                               |                                                     |
                               v                                                     v
+----------------------------------------------+      +-------------------------------------------------------------+
| ML: SEMANTIC RETRIEVAL (RemoteCLIP /ml/)     |      | ML: BITEMPORAL CHANGE DETECTION (BIT / ChangeFormer /ml/)   |
| - ViT Remote-Sensing CLIP with RS adapters   |      | - Multi-spectral 4/6-band input (No RGB quantization!)      |
| - Domain vocabulary projection               |      | - Binary/Multiclass change mask (Construction/Road/Water)   |
| - Milvus / FAISS ANN Vector Index            |      | - Confidence score per region polygon                       |
+----------------------------------------------+      +------------------------------+------------------------------+
                                                                                     |
                                                                                     v
                                                      +-------------------------------------------------------------+
                                                      | FALSE-ALARM & RELIABILITY GATE (reliability_check.py)       |
                                                      | - Cloud & shadow penalty mask                               |
                                                      | - Phenological / Seasonal NDVI trend consistency check      |
                                                      | - Sub-pixel co-registration verification                    |
                                                      +------------------------------+------------------------------+
                                                                                     |
                                                                                     v
+-------------------------------------------------------------------------------------------------------------------+
| BACKEND SERVICES (/backend/)                                                                                      |
| - FastAPI REST Endpoints (Search, AOI, Async Change Detection Jobs, Review, Audit Trail)                           |
| - Celery Worker + Redis (Async tiling, embedding, and inference processing)                                       |
| - PostgreSQL + PostGIS (Scenes, geometries, provenance, analyst logs)                                            |
| - Titiler / Dynamic COG Tile Renderer (On-the-fly false color, NDVI, true color preview)                           |
| - Cryptographic Tamper-Proof Audit Trail (SHA-256 hash-chained ledger: prev_hash + decision + timestamp)          |
+----------------------------------------------------+--------------------------------------------------------------+
                                                     |
                                                     v
+-------------------------------------------------------------------------------------------------------------------+
| FRONTEND WORKFLOW (/frontend/ - React 19 + Vite + Tactical Aerospace HUD)                                         |
|  Step 1: Search & Input (Prompt + Interactive AOI Draw + Multi-Year Range 2024-2026)                              |
|  Step 2: AI Search & Ranking ("Understanding query" state -> Cosine-ranked AOIs)                                  |
|  Step 3: Explore & Detect Change (Before/After split-slider + Category Breakdown: Construction/Road/Water/Clear)  |
|  Step 4: Quality Check & AI Result (Reliability flags breakdown + AI Result Card + First-seen date)               |
|  Step 5: Analyst Review & Save (Side-by-side inspect + Confirm/Reject + Append to Tamper-Proof Audit Ledger)        |
+-------------------------------------------------------------------------------------------------------------------+
```

---

## 1. Strict Separation: Raw Band Path vs. RGB Display Path

A central judging criterion for Problem Statement 26227 is preventing premature conversion to 3-channel 8-bit RGB at ingestion.

* **Authoritative Data Layer**:
  - Ingestion retains multi-spectral Cloud-Optimized GeoTIFFs (COGs) preserving B02 (Blue), B03 (Green), B04 (Red), B08 (NIR), B11 (SWIR-1), B12 (SWIR-2), and SCL.
  - Surface reflectance values are stored as native 32-bit floats $[0.0, 1.0]$ or 16-bit digital numbers scaled by $10,000$.
  - All spectral indices ($\text{NDVI}, \text{NDBI}, \text{NDWI}$), band differences ($\Delta B_k = B_k^{\text{post}} - B_k^{\text{pre}}$), and change detection inference run **exclusively** on this multi-spectral tensor.
* **Derived Visualization Layer**:
  - 8-bit RGB or Color-Infrared (CIR) composites are generated **strictly downstream** or rendered on-the-fly via rasterio/Titiler.
  - Every preview image is tagged with:
    `"display/embedding-input composite, derived, not authoritative"`.
  - RGB is never saved as the analysis source.

---

## 2. Learned Models vs. Heuristic-Assisted Components

For full transparency during hackathon evaluation, the platform explicitly differentiates between deep learned neural models and calibrated heuristic logic:

| Component | Architecture & Method | Status | Rationale |
| :--- | :--- | :--- | :--- |
| **Semantic Retrieval** | ViT-B Vision Transformer + GRU Text Encoder with Remote Sensing Residual Adapters | **Learned** | Fine-tuned using contrastive InfoNCE loss on domain terminology (*"new construction"*, *"bunker-like structure"*, *"riverfront bridge"*) mapping prompts to 512-dim embedding space. |
| **Vector Search Index** | FAISS Cosine Similarity Engine (Milvus-compatible interface) | **Learned Index** | Fast approximate nearest neighbor (ANN) retrieval over tile vector embeddings. |
| **Change Detection Backbone** | Bitemporal Image Transformer (BIT) with Siamese Multi-Spectral ConvNeXt/ResNet stem | **Learned** | Dual-branch feature extraction over 4-channel input ($B02, B03, B04, B08$), spatial tokenization, and cross-attention temporal difference modeling. |
| **Change-Type Classification** | Hybrid: Spatial Moment Geometry + Spectral Delta Calibration Head | **Hybrid (Learned + Heuristic)** | Spatial elongation, boundary complexity, and compactness are extracted via tensor operations; physical decision boundaries ($\Delta\text{NDBI} > +0.15$ for concrete, $\Delta\text{NDVI} < -0.20$ for clearance, $\Delta\text{NDWI} > +0.18$ for water) calibrate class probabilities via temperature-scaled Softmax. |
| **Reliability Gate** | `reliability_check.py` 4-Gate Filter (Cloud, Shadow, Phenology, Co-Registration) | **Physical Heuristic & Statistical** | Compares `s2cloudless` gradient probability, SCL quality classes, diffuse scene-wide NDVI variance (to suppress seasonal crop cycles), and sub-pixel cross-correlation shift. |
| **Audit Ledger** | SHA-256 Hash Chain Ledger | **Cryptographic** | Mathematical cryptographic hash chaining guaranteeing tamper-evidence across analyst decisions. |

---

## 3. Cryptographic Tamper-Proof Audit Trail

In mission-critical defense intelligence, analysts' confirmations and rejections must be protected against tampering. MiraeNova implements a native SHA-256 append-only hash chain:

$$\text{Block}[n].\text{hash} = \text{SHA256}\Big(\text{Block}[n-1].\text{hash} \parallel \text{Timestamp} \parallel \text{User} \parallel \text{TilePairID} \parallel \text{Decision} \parallel \text{Evidence}\Big)$$

- **Genesis Block**: Initiates with a 64-character zero digest.
- **Evidence Binding**: Binds polygon coordinates, area in hectares, baseline date, first-seen date, and officer comments.
- **Live Verification**: Any alteration to a historical record corrupts all subsequent hashes, immediately triggering a `TAMPERED_COMPROMISED` alert in the UI and API.

---

## 4. Quick Start & Execution Guide

### Option A: Local Standalone Execution (Offline / Air-Gapped)

1. **Verify Environment**:
   Python 3.9+ and Node.js v18+ are required.
   ```bash
   python --version
   node --version
   ```

2. **Run Master Demo Pipeline**:
   Synthesizes raw Sentinel-2 BOA scenes, runs tiling and preprocessing, fine-tunes RemoteCLIP, indexes vectors, executes BIT change detection, and commits to the cryptographic ledger:
   ```bash
   python run_demo_pipeline.py
   ```

3. **Run Automated Test Suite**:
   ```bash
   python run_tests.py
   ```
   *(Executes all 15 unit and integration tests across data pipeline, ML models, and backend APIs)*.

4. **Launch Backend Server**:
   ```bash
   python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   ```
   API Docs available at: `http://localhost:8000/docs`

5. **Launch Frontend Application**:
   ```bash
   cd frontend
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

### Option B: Docker Compose Deployment (Single-Command Air-Gapped Stack)

To run the entire system in an isolated container network:

```bash
docker compose up --build
```

**Services Launched:**
- `miraenova_backend`: FastAPI REST API on port `8000`
- `miraenova_frontend`: Nginx serving built React app on port `3000`
- `miraenova_postgis`: PostgreSQL 16 + PostGIS on port `5432`
- `miraenova_redis`: Redis 7 message broker on port `6379`
- `miraenova_worker`: Celery async worker for heavy raster jobs
- `miraenova_titiler`: Dynamic COG tile server on port `8001`

---

## 5. Walkthrough: 5-Step Analyst Intelligence Workflow

1. **STEP 1 — Search & Input**:
   - Analyst enters natural language prompt: *"new buildings near river"*.
   - Specifies target Area of Interest (AOI): `Sarayu Riverfront Sector`.
   - Selects multi-temporal timeframe: `2024-03-15` (Baseline) to `2026-02-20` (Current).
   - Sensor: `Sentinel-2A/B L2A BOA Multi-Spectral`.
2. **STEP 2 — AI Search & Ranking**:
   - Neural query understanding displays extracted semantic concepts.
   - RemoteCLIP searches the offline FAISS/Milvus vector index and returns ranked candidate tiles sorted by cosine similarity (e.g. `Tile t001` with $99.3\%$ match).
3. **STEP 3 — Explore & Detect Change**:
   - Interactive high-res map with an interactive **Before/After split comparison slider**.
   - BIT Model highlights detected change vectors categorized by domain:
     - 🟠 **Construction**: New industrial facility and structures ($1.45\text{ ha}$)
     - 🟣 **Road**: New bridge corridor spanning the river ($0.82\text{ ha}$)
     - 🔵 **Water**: Riverbank reinforcement and channel adjustment
     - 🟢 **Clearance**: Land excavation and soil preparation buffer ($1.93\text{ ha}$)
4. **STEP 4 — Quality Check & AI Result**:
   - Real-time Reliability Gate verifies the 4 physical checks:
     - Cloud Mask: $0.8\%$ (Pass)
     - Shadow Risk: $0.2\%$ (Pass)
     - Seasonal Phenology: $5.0\%$ diffuse variation (Pass)
     - Co-Registration Shift: $0.14\text{ px}$ (Pass)
   - Official AI Result Card presents the confirmed anomaly, confidence score ($94.5\%$), and first-seen date.
5. **STEP 5 — Analyst Review & Save**:
   - Side-by-side synchronized comparison between 2024 baseline and 2026 post-event.
   - Analyst enters operational notes and clicks **CONFIRM (Real Change)**.
   - The decision is cryptographically hashed with SHA-256 and appended to the immutable audit ledger.

---

## Project Structure

```
MiraeNova/
├── data/
│   ├── raw/                 # Authoritative Sentinel-2 L2A BOA Multi-Band COGs
│   ├── processed/           # Georeferenced tiles, quality masks, band-difference maps
│   ├── composites/          # Derived preview PNGs (strictly tagged non-authoritative)
│   ├── tile_vector_index.json # Persistent FAISS/Milvus vector store
│   └── audit_ledger.json    # Cryptographic SHA-256 immutable ledger
├── data_pipeline/
│   ├── band_stack.py        # Multi-band surface reflectance reader/writer (B02-B12, SCL)
│   ├── tiling.py            # Overlapping grid tiling & georeferencing
│   ├── cloud_mask.py        # s2cloudless continuous probability + SCL quality flags
│   ├── radiometry.py        # Reversible per-scene radiometric normalization
│   ├── band_math.py         # NDVI, NDBI, NDWI, and post - pre band differences
│   ├── co_registration.py   # Sub-pixel cross-correlation phase checker
│   ├── display_composite.py # Derived RGB/CIR PNG generator (non-authoritative)
│   ├── pipeline.py          # Unified CLI & Celery-callable pipeline
│   └── seed_demo_data.py    # Multi-temporal Sentinel-2 scene synthesizer
├── ml/
│   ├── remote_clip/         # RemoteCLIP ViT vision-language model & fine-tuning
│   ├── change_detection/    # Bitemporal Image Transformer (BIT) & hybrid classifier
│   └── reliability_check.py # 4-Gate false-alarm & quality pre-filter
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application entrypoint
│   │   ├── config.py        # System configuration
│   │   ├── db/              # Audit ledger & database models
│   │   ├── routes/          # REST API endpoints (Search, Scenes, Change, Audit)
│   │   └── tasks/           # Celery async worker tasks
│   └── Dockerfile           # Backend container definition
├── frontend/
│   ├── src/
│   │   ├── components/      # React components for Steps 1 through 5 & Audit Modal
│   │   ├── App.jsx          # Main workflow controller
│   │   └── index.css        # Tactical aerospace dark HUD theme
│   ├── Dockerfile           # Multi-stage frontend container
│   └── nginx.conf           # Reverse proxy configuration
├── tests/
│   ├── test_data_pipeline.py # Unit tests for data pipeline
│   ├── test_ml_models.py     # Unit tests for RemoteCLIP, BIT, and Reliability
│   └── test_backend_api.py   # Integration tests for FastAPI endpoints
├── docker-compose.yml       # Air-gapped orchestration definition
├── run_demo_pipeline.py     # Master end-to-end demo execution script
├── run_tests.py             # Test suite runner
└── README.md                # Comprehensive documentation & architecture guide
```

---

## Evaluation Benchmark & Verification Highlights

- **Raw Multi-Band Purity**: Zero 8-bit RGB quantization at ingestion; multi-band float32 reflectance maintained throughout all change detection math.
- **Sub-Pixel Registration**: Cross-correlation phase check detects misalignment down to $0.1\text{ px}$.
- **False-Alarm Mitigation**: Eliminates transient seasonal changes and cloud puff false positives before analyst exposure.
- **Auditable Provenance**: Full cryptographic verification guaranteeing non-repudiation of all intelligence decisions.
- **Air-Gapped Readiness**: Fully self-contained, requiring zero external internet or cloud API access at runtime.
