"""
Default embeddings implementations for momo-kb.

This module provides local embeddings that work on any device without requiring
external API keys or internet connections.
"""

from typing import Optional
from langchain_core.embeddings import Embeddings

# Global cached instance to avoid reloading models
_default_embeddings_instance: Optional[Embeddings] = None


def get_default_embeddings() -> Optional[Embeddings]:
    """
    Get the default local embeddings model if available.

    Uses all-MiniLM-L6-v2 via LangChain HuggingFace integration.
    This model is:
    - Small (~22MB)
    - Fast on CPU
    - Good quality for general text
    - Runs locally without API keys

    Returns:
        Embeddings: Ready-to-use embeddings instance, or None if dependencies not available
    """
    global _default_embeddings_instance

    if _default_embeddings_instance is None:
        try:
            # Try to use HuggingFace via LangChain integration
            from langchain_huggingface import HuggingFaceEmbeddings

            _default_embeddings_instance = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )

        except ImportError:
            try:
                # Fallback to direct sentence-transformers if LangChain integration not available
                from langchain_core.embeddings import Embeddings as BaseEmbeddings
                from sentence_transformers import SentenceTransformer
                import numpy as np
                from typing import List

                class SentenceTransformerEmbeddings(BaseEmbeddings):
                    """Direct sentence-transformers wrapper."""

                    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
                        self.model = SentenceTransformer(model_name)

                    def embed_documents(self, texts: List[str]) -> List[List[float]]:
                        """Embed search documents."""
                        embeddings = self.model.encode(texts, normalize_embeddings=True)
                        return embeddings.tolist()

                    def embed_query(self, text: str) -> List[float]:
                        """Embed query text."""
                        embedding = self.model.encode([text], normalize_embeddings=True)
                        return embedding[0].tolist()

                _default_embeddings_instance = SentenceTransformerEmbeddings()

            except ImportError:
                # No embeddings available - will fall back to document search
                _default_embeddings_instance = None

    return _default_embeddings_instance


def create_local_embeddings(model_name: str = "all-MiniLM-L6-v2") -> Embeddings:
    """
    Create a local embeddings instance with a specific model.

    Args:
        model_name: HuggingFace model name for sentence transformers

    Returns:
        Embeddings: Local embeddings instance
    """
    try:
        from langchain_huggingface import HuggingFaceEmbeddings

        return HuggingFaceEmbeddings(
            model_name=f"sentence-transformers/{model_name}",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    except ImportError:
        # Direct sentence-transformers fallback
        from langchain_core.embeddings import Embeddings as BaseEmbeddings
        from sentence_transformers import SentenceTransformer
        from typing import List

        class CustomSentenceTransformerEmbeddings(BaseEmbeddings):
            """Custom sentence-transformers wrapper."""

            def __init__(self, model_name: str):
                self.model = SentenceTransformer(model_name)

            def embed_documents(self, texts: List[str]) -> List[List[float]]:
                """Embed search documents."""
                embeddings = self.model.encode(texts, normalize_embeddings=True)
                return embeddings.tolist()

            def embed_query(self, text: str) -> List[float]:
                """Embed query text."""
                embedding = self.model.encode([text], normalize_embeddings=True)
                return embedding[0].tolist()

        return CustomSentenceTransformerEmbeddings(model_name)


# Available local models with their characteristics
LOCAL_MODELS = {
    "all-MiniLM-L6-v2": {
        "size": "22MB",
        "speed": "fast",
        "quality": "good",
        "description": "Best balance of speed and quality for general use",
    },
    "all-mpnet-base-v2": {
        "size": "420MB",
        "speed": "medium",
        "quality": "excellent",
        "description": "Higher quality but larger model",
    },
    "paraphrase-MiniLM-L3-v2": {
        "size": "17MB",
        "speed": "very fast",
        "quality": "good",
        "description": "Smallest and fastest, good for development",
    },
}


def list_local_models():
    """List available local embedding models with their characteristics."""
    return LOCAL_MODELS
