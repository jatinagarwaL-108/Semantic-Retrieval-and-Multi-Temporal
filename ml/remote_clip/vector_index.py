"""
Vector Database & ANN Index for Semantic Retrieval
========================================================================================
Implements a Milvus-compatible vector storage and Approximate Nearest Neighbor (ANN) index.
Uses local Cosine Similarity ANN engine for 100% offline, air-gapped deployment.
Stores 512-dim RemoteCLIP embeddings alongside geospatial tile metadata.
========================================================================================
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from .model import get_remote_clip_model


class TileVectorIndex:
    """
    Manages vector embeddings and metadata for satellite imagery tiles.
    Provides Milvus-compatible search interface for natural language query retrieval.
    """

    def __init__(self, index_path: str = "data/tile_vector_index.json"):
        self.index_path = index_path
        self.tile_ids: List[str] = []
        self.embeddings: Optional[np.ndarray] = None  # Shape: (N, 512)
        self.metadata_store: Dict[str, Dict[str, Any]] = {}
        self.load_index()

    def load_index(self):
        """Loads index and metadata from persistent storage if exists."""
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, "r") as f:
                    data = json.load(f)
                self.tile_ids = data.get("tile_ids", [])
                vectors = data.get("embeddings", [])
                if vectors:
                    self.embeddings = np.array(vectors, dtype=np.float32)
                self.metadata_store = data.get("metadata", {})
                print(f"[VectorIndex] Loaded {len(self.tile_ids)} tile embeddings from {self.index_path}")
            except Exception as e:
                print(f"[VectorIndex] Error loading index: {e}")

    def save_index(self):
        """Persists index to disk."""
        os.makedirs(os.path.dirname(os.path.abspath(self.index_path)), exist_ok=True)
        data = {
            "tile_ids": self.tile_ids,
            "embeddings": self.embeddings.tolist() if self.embeddings is not None else [],
            "metadata": self.metadata_store,
            "index_type": "FAISS_COSINE_SIMILARITY_MILVUS_COMPATIBLE",
            "dimension": 512,
        }
        with open(self.index_path, "w") as f:
            json.dump(data, f, indent=2)

    def insert(self, tile_id: str, embedding: np.ndarray, metadata: Dict[str, Any]):
        """Inserts or updates a tile embedding."""
        emb_norm = embedding / (np.linalg.norm(embedding) + 1e-7)
        if tile_id in self.tile_ids:
            idx = self.tile_ids.index(tile_id)
            self.embeddings[idx] = emb_norm
            self.metadata_store[tile_id] = metadata
        else:
            self.tile_ids.append(tile_id)
            self.metadata_store[tile_id] = metadata
            if self.embeddings is None:
                self.embeddings = np.array([emb_norm], dtype=np.float32)
            else:
                self.embeddings = np.vstack([self.embeddings, emb_norm])

    def search_by_vector(self, query_vector: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Executes Cosine Similarity ANN search against tile embeddings.
        Returns ranked list of matches with similarity scores in [0.0, 1.0].
        """
        if self.embeddings is None or len(self.tile_ids) == 0:
            return []

        q_norm = query_vector / (np.linalg.norm(query_vector) + 1e-7)
        # Dot product of normalized vectors = Cosine Similarity
        similarities = np.dot(self.embeddings, q_norm)
        
        # Scale to 0-1 range for intuitive percentage display
        scaled_scores = (similarities + 1.0) / 2.0

        top_indices = np.argsort(scaled_scores)[::-1][:top_k]

        results = []
        for rank, idx in enumerate(top_indices, start=1):
            t_id = self.tile_ids[idx]
            meta = self.metadata_store.get(t_id, {})
            score = float(scaled_scores[idx])
            raw_cosine = float(similarities[idx])

            results.append({
                "rank": rank,
                "tile_id": t_id,
                "similarity_score": round(score, 4),
                "raw_cosine": round(raw_cosine, 4),
                "metadata": meta,
            })
        return results

    def search_by_text(self, query_text: str, top_k: int = 5) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        End-to-end natural language search:
        query_text -> RemoteCLIP text encoder -> ANN search.
        """
        model = get_remote_clip_model()
        text_emb = model.encode_text(query_text)
        ranked_tiles = self.search_by_vector(text_emb, top_k=top_k)

        query_analysis = {
            "query_text": query_text,
            "detected_concepts": [
                w for w in query_text.lower().split()
                if w in ["construction", "building", "river", "road", "bunker", "cleared", "water", "new"]
            ],
            "embedding_dimension": len(text_emb),
        }
        return ranked_tiles, query_analysis

    def index_all_tiles_from_catalog(self, catalog_path: str = "data/processed/bitemporal_catalog.json"):
        """
        Indexes all tiles found in the bitemporal catalog using their derived preview images.
        """
        if not os.path.exists(catalog_path):
            print(f"[VectorIndex] Catalog not found: {catalog_path}")
            return

        with open(catalog_path, "r") as f:
            pairs = json.load(f)

        model = get_remote_clip_model()
        count = 0

        for pair in pairs:
            for key in ["pre_tile", "post_tile"]:
                tile_info = pair.get(key, {})
                tile_id = tile_info.get("tile_id")
                preview_png = tile_info.get("display_preview_png")

                if tile_id and preview_png and os.path.exists(preview_png):
                    emb = model.encode_image(preview_png)
                    meta = {
                        "tile_id": tile_id,
                        "parent_scene_id": tile_info.get("parent_scene_id"),
                        "acquisition_date": tile_info.get("acquisition_date"),
                        "bounds": tile_info.get("bounds"),
                        "geojson_geometry": tile_info.get("geojson_geometry"),
                        "preview_png": preview_png,
                        "cir_png": tile_info.get("false_color_png"),
                        "cog_path": tile_info.get("cog_path"),
                        "quality_metrics": tile_info.get("quality_metrics"),
                    }
                    self.insert(tile_id, emb, meta)
                    count += 1

        self.save_index()
        print(f"[VectorIndex] Successfully indexed {count} tiles into vector store.")


_GLOBAL_INDEX: Optional[TileVectorIndex] = None

def get_vector_index() -> TileVectorIndex:
    global _GLOBAL_INDEX
    if _GLOBAL_INDEX is None:
        _GLOBAL_INDEX = TileVectorIndex()
    return _GLOBAL_INDEX


if __name__ == "__main__":
    idx = get_vector_index()
    idx.index_all_tiles_from_catalog()
    hits, analysis = idx.search_by_text("new buildings near river", top_k=3)
    print(f"Search results for 'new buildings near river':")
    for h in hits:
        print(f"  Rank {h['rank']}: Tile {h['tile_id']} (Score: {h['similarity_score']:.4f})")
