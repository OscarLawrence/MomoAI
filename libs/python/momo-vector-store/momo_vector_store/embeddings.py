"""
Local embeddings implementation that works without external dependencies.

Provides a simple but effective embedding model for development and basic use cases.
"""

import hashlib
import math
from typing import List, Dict, Optional, Any
from langchain_core.embeddings import Embeddings


class LocalEmbeddings(Embeddings):
    """
    Local embeddings implementation using TF-IDF-like approach.

    This implementation provides semantic embeddings without requiring
    external models or dependencies. It's suitable for development,
    testing, and basic production use cases.

    Features:
    - No external dependencies
    - Deterministic embeddings
    - Reasonable semantic similarity
    - Fast computation
    - Works on any machine
    """

    def __init__(self, dimension: int = 384):
        """
        Initialize local embeddings.

        Args:
            dimension: Embedding vector dimension (default: 384)
        """
        self.dimension = dimension
        self.vocabulary: Dict[str, int] = {}
        self.word_frequencies: Dict[str, int] = {}
        self.document_count = 0

        # Common stop words to filter
        self.stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "should",
            "could",
            "can",
            "may",
            "might",
            "must",
            "this",
            "that",
            "these",
            "those",
        }

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple documents."""
        if not texts:
            return []

        # Update vocabulary and frequencies
        self._update_vocabulary(texts)

        # Generate embeddings for each document
        embeddings = []
        for text in texts:
            embedding = self._generate_embedding(text)
            embeddings.append(embedding)

        return embeddings

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a single query."""
        return self._generate_embedding(text)

    def _update_vocabulary(self, texts: List[str]) -> None:
        """Update vocabulary and word frequencies from texts."""
        for text in texts:
            words = self._preprocess_text(text)
            self.document_count += 1

            # Track unique words in this document
            doc_words = set()

            for word in words:
                if word not in self.vocabulary:
                    self.vocabulary[word] = len(self.vocabulary)

                # Count document frequency (not term frequency)
                if word not in doc_words:
                    self.word_frequencies[word] = self.word_frequencies.get(word, 0) + 1
                    doc_words.add(word)

    def _preprocess_text(self, text: str) -> List[str]:
        """Preprocess text into normalized word list."""
        # Convert to lowercase and split
        words = text.lower().split()

        # Remove punctuation and filter stop words
        clean_words = []
        for word in words:
            # Remove punctuation
            clean_word = "".join(c for c in word if c.isalnum())

            # Filter out stop words and very short words
            if clean_word and len(clean_word) > 2 and clean_word not in self.stop_words:
                clean_words.append(clean_word)

        return clean_words

    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text using TF-IDF-like approach."""
        words = self._preprocess_text(text)

        if not words:
            return [0.0] * self.dimension

        # Count term frequencies in this document
        word_counts: Dict[str, int] = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1

        # Initialize embedding vector
        embedding = [0.0] * self.dimension

        # Generate embedding using combination of approaches
        for word, count in word_counts.items():
            if word in self.vocabulary:
                # Calculate TF-IDF-like weight
                tf = count / len(words)  # Term frequency
                df = self.word_frequencies.get(word, 1)  # Document frequency
                idf = math.log(max(self.document_count, 1) / df) if df > 0 else 1.0
                weight = tf * idf

                # Map word to multiple dimensions using hash functions
                word_hash = int(hashlib.md5(word.encode()).hexdigest(), 16)

                # Distribute word contribution across multiple dimensions
                for i in range(
                    min(8, self.dimension)
                ):  # Use up to 8 dimensions per word
                    dim_index = (word_hash + i * 1000) % self.dimension

                    # Add positional and semantic information
                    semantic_value = (word_hash % 1000) / 1000.0  # 0-1 range
                    position_weight = 1.0 / (i + 1)  # Earlier positions get more weight

                    embedding[dim_index] += weight * semantic_value * position_weight

        # Normalize the embedding vector (handle NaN and zero vectors)
        magnitude = math.sqrt(sum(x * x for x in embedding))
        if magnitude > 1e-10:  # Avoid division by very small numbers
            embedding = [x / magnitude for x in embedding]
        else:
            # Handle zero or near-zero vectors by creating a small random-like vector
            embedding = [
                0.1 * ((i + 1) / self.dimension) for i in range(self.dimension)
            ]

        # Ensure no NaN values
        embedding = [
            x if not (math.isnan(x) or math.isinf(x)) else 0.1 for x in embedding
        ]

        return embedding

    def get_stats(self) -> Dict[str, Any]:
        """Get embedding statistics."""
        return {
            "vocabulary_size": len(self.vocabulary),
            "document_count": self.document_count,
            "dimension": self.dimension,
            "model_type": "local_tfidf",
        }


class SimpleEmbeddings(Embeddings):
    """
    Simplified embeddings for very basic use cases.

    Even simpler than LocalEmbeddings, using only word hashing.
    Suitable for testing and demonstrations.
    """

    def __init__(self, dimension: int = 128):
        """Initialize simple embeddings."""
        self.dimension = dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate simple embeddings for documents."""
        return [self._hash_embedding(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """Generate simple embedding for query."""
        return self._hash_embedding(text)

    def _hash_embedding(self, text: str) -> List[float]:
        """Generate embedding using word hashing."""
        words = text.lower().split()

        if not words:
            return [0.0] * self.dimension

        # Initialize embedding
        embedding = [0.0] * self.dimension

        # Add contribution from each word
        for i, word in enumerate(words[:20]):  # Limit to first 20 words
            word_hash = int(hashlib.md5(word.encode()).hexdigest(), 16)

            # Map to dimensions
            for j in range(min(4, self.dimension)):  # 4 dimensions per word
                dim_index = (word_hash + j * 100) % self.dimension
                value = ((word_hash + j) % 1000) / 1000.0
                position_weight = 1.0 / (i + 1)

                embedding[dim_index] += value * position_weight

        # Simple normalization
        max_val = max(abs(x) for x in embedding) if embedding else 1.0
        if max_val > 0:
            embedding = [x / max_val for x in embedding]

        return embedding
