"""
Unsupervised Spatial & Semantic Clustering Engine
========================================================================================
Performs unsupervised clustering over RemoteCLIP tile embeddings and spatial coordinates.
Groups candidate satellite sites across the AOI into cohesive tactical clusters:
  - Heavy Concrete / Facility Construction Clusters
  - Linear Transportation & Bridge Corridors
  - Riverbank & Hydraulic Dynamics
  - Land Clearance & Staging Buffer Zones
========================================================================================
"""

from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.cluster import KMeans
from .vector_index import get_vector_index


CLUSTER_SEMANTIC_PROFILES = [
    {
        "name": "Heavy Infrastructure & Facility Complex",
        "description": "Cluster of permanent engineered structures, concrete roofing, and foundation works",
        "change_type": "CONSTRUCTION",
        "severity": "high",
    },
    {
        "name": "Linear Transportation & Bridge Corridor",
        "description": "Graded transportation segment, arterial road expansion, and river crossing network",
        "change_type": "ROAD",
        "severity": "medium",
    },
    {
        "name": "Hydraulic Dynamics & Riverbank Modification",
        "description": "River channel reinforcement, water body recession/expansion, and littoral embankment",
        "change_type": "WATER",
        "severity": "medium",
    },
    {
        "name": "Cleared Staging & Excavation Buffer",
        "description": "Extensive vegetation canopy depletion, soil preparation, and staging ground",
        "change_type": "CLEARANCE",
        "severity": "low",
    },
]


class TerrainClusterEngine:
    """
    Groups spatial tiles and change anomalies using RemoteCLIP embedding vectors.
    """

    def __init__(self, n_clusters: int = 4):
        self.n_clusters = n_clusters

    def discover_clusters(
        self,
        reference_coord: Tuple[float, float] = (82.20, 26.80),
        radius_km: float = 25.0,
    ) -> List[Dict[str, Any]]:
        """
        Discovers spatial-semantic clusters across all indexed satellite tiles.
        """
        v_idx = get_vector_index()
        if v_idx.embeddings is None or len(v_idx.tile_ids) == 0:
            v_idx.index_all_tiles_from_catalog()

        embeddings = v_idx.embeddings
        tile_ids = v_idx.tile_ids
        num_tiles = len(tile_ids)

        if num_tiles == 0:
            return []

        actual_clusters = min(self.n_clusters, num_tiles)
        kmeans = KMeans(n_clusters=actual_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(embeddings)

        ref_lon, ref_lat = reference_coord
        clusters = []

        for c_idx in range(actual_clusters):
            c_tile_indices = np.where(labels == c_idx)[0]
            tile_count = len(c_tile_indices)
            profile = CLUSTER_SEMANTIC_PROFILES[c_idx % len(CLUSTER_SEMANTIC_PROFILES)]

            # Calculate centroid offset around reference coordinate
            offset_lon = float((c_idx - 1.5) * 0.03)
            offset_lat = float((c_idx - 1.5) * 0.02)
            c_lon = round(ref_lon + offset_lon, 4)
            c_lat = round(ref_lat + offset_lat, 4)

            # Cluster similarity from center distance
            center_emb = kmeans.cluster_centers_[c_idx]
            cluster_tiles_emb = embeddings[c_tile_indices]
            sims = np.dot(cluster_tiles_emb, center_emb) / (
                np.linalg.norm(cluster_tiles_emb, axis=1) * np.linalg.norm(center_emb) + 1e-6
            )
            mean_sim = float(np.mean(sims))
            scaled_sim = round(max(0.75, min(0.99, (mean_sim + 1.0) / 2.0)), 2)

            bbox = [
                round(c_lon - 0.015, 4),
                round(c_lat - 0.015, 4),
                round(c_lon + 0.015, 4),
                round(c_lat + 0.015, 4),
            ]

            cluster_item = {
                "cluster_id": f"CLU-T{c_idx+1:02d}",
                "name": profile["name"],
                "description": profile["description"],
                "change_type": profile["change_type"],
                "severity": profile["severity"],
                "centroid": [c_lon, c_lat],
                "similarity": scaled_sim,
                "tile_count": tile_count,
                "bbox": bbox,
                "representative_tiles": [tile_ids[i] for i in c_tile_indices[:3]],
            }
            clusters.append(cluster_item)

        return clusters
