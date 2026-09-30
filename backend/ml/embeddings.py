from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

# Load all-MiniLM-L6-v2 model (~80MB, fast and CPU-optimized)
MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer = None


def get_model() -> SentenceTransformer:
    """Lazy load the sentence transformer model to prevent unnecessary overhead at import time."""
    global _model
    if _model is None:
        try:
            _model = SentenceTransformer(MODEL_NAME, local_files_only=True)
        except Exception:
            _model = SentenceTransformer(MODEL_NAME)
    return _model


def format_alert_text(alert) -> str:
    """Construct a composite context string for an alert combining key contextual fields."""
    return f"{alert.event_type} | user:{alert.username} | asset:{alert.target_asset} | {alert.raw_message}"


def generate_embeddings(alerts: List) -> np.ndarray:
    """Generates normalized dense embeddings for a list of alert DB models or objects.
    
    Batches the encoding process for optimal CPU throughput and normalizes embeddings
    so cosine similarity can be computed via efficient dot products.
    """
    if not alerts:
        return np.empty((0, 384), dtype=np.float32)

    model = get_model()
    texts = [format_alert_text(a) for a in alerts]

    embeddings = model.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return embeddings
