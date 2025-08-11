"""
Embedding Engine - Lightweight embedding generation without external dependencies.

Provides simple but effective text embeddings using TF-IDF and dimensionality reduction.
Designed for fast prototyping and to avoid heavy dependencies.
"""

import numpy as np
from typing import Dict, List, Optional, Set
from collections import Counter, defaultdict
import re
import math


class SimpleEmbeddingEngine:
    """
    Lightweight embedding engine using TF-IDF with SVD dimensionality reduction.
    
    While not as sophisticated as transformer models, this provides:
    1. No external dependencies
    2. Fast computation
    3. Deterministic results
    4. Good baseline performance for document similarity
    """
    
    def __init__(self, dimension: int = 384, max_features: int = 10000):
        """
        Initialize embedding engine.
        
        Args:
            dimension: Target embedding dimension
            max_features: Maximum vocabulary size
        """
        self.dimension = dimension
        self.max_features = max_features
        
        # Vocabulary and IDF weights
        self._vocabulary: Dict[str, int] = {}
        self._idf_weights: np.ndarray = None
        self._svd_components: np.ndarray = None
        self._is_fitted = False
        
        # Simple stopwords (can be expanded)
        self._stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
            'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their'
        }
        
    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization with basic preprocessing.
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        # Convert to lowercase and extract words
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        
        # Filter stopwords and short tokens
        tokens = [
            token for token in tokens 
            if token not in self._stopwords and len(token) > 2
        ]
        
        return tokens
        
    def fit(self, documents: List[str]) -> None:
        """
        Fit the embedding engine on a corpus of documents.
        
        Args:
            documents: List of document texts
        """
        if not documents:
            raise ValueError("Cannot fit on empty document list")
            
        # Tokenize all documents
        tokenized_docs = [self._tokenize(doc) for doc in documents]
        
        # Build vocabulary
        word_counts = Counter()
        for tokens in tokenized_docs:
            word_counts.update(set(tokens))  # Count document frequency, not term frequency
            
        # Select top words by document frequency
        top_words = word_counts.most_common(self.max_features)
        self._vocabulary = {word: idx for idx, (word, _) in enumerate(top_words)}
        vocab_size = len(self._vocabulary)
        
        if vocab_size == 0:
            raise ValueError("No valid vocabulary found")
            
        # Compute TF-IDF matrix
        tfidf_matrix = np.zeros((len(documents), vocab_size), dtype=np.float32)
        
        for doc_idx, tokens in enumerate(tokenized_docs):
            # Compute term frequencies
            term_counts = Counter(tokens)
            doc_length = len(tokens)
            
            for term, count in term_counts.items():
                if term in self._vocabulary:
                    vocab_idx = self._vocabulary[term]
                    tf = count / doc_length  # Term frequency
                    tfidf_matrix[doc_idx, vocab_idx] = tf
                    
        # Compute IDF weights
        doc_frequencies = np.sum(tfidf_matrix > 0, axis=0)
        self._idf_weights = np.log(len(documents) / (doc_frequencies + 1))
        
        # Apply IDF weights
        tfidf_matrix *= self._idf_weights
        
        # Dimensionality reduction with SVD if needed
        if vocab_size > self.dimension:
            # Center the data
            mean_vector = np.mean(tfidf_matrix, axis=0)
            centered_matrix = tfidf_matrix - mean_vector
            
            # SVD
            U, s, Vt = np.linalg.svd(centered_matrix.T, full_matrices=False)
            
            # Keep top components
            self._svd_components = U[:, :self.dimension]
            self._mean_vector = mean_vector
        else:
            # Pad with zeros if vocabulary is smaller than target dimension
            self._svd_components = np.eye(vocab_size, self.dimension)
            self._mean_vector = np.zeros(vocab_size)
            
        self._is_fitted = True
        
    def embed(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
            
        Raises:
            RuntimeError: If engine is not fitted
        """
        if not self._is_fitted:
            raise RuntimeError("Embedding engine must be fitted before use")
            
        tokens = self._tokenize(text)
        
        # Compute TF vector
        tf_vector = np.zeros(len(self._vocabulary), dtype=np.float32)
        if tokens:
            term_counts = Counter(tokens)
            doc_length = len(tokens)
            
            for term, count in term_counts.items():
                if term in self._vocabulary:
                    vocab_idx = self._vocabulary[term]
                    tf_vector[vocab_idx] = count / doc_length
                    
        # Apply IDF weights
        tfidf_vector = tf_vector * self._idf_weights
        
        # Apply dimensionality reduction
        centered_vector = tfidf_vector - self._mean_vector
        embedding = np.dot(centered_vector, self._svd_components)
        
        # Ensure correct dimension
        if embedding.shape[0] < self.dimension:
            # Pad with zeros
            padded = np.zeros(self.dimension, dtype=np.float32)
            padded[:embedding.shape[0]] = embedding
            embedding = padded
        elif embedding.shape[0] > self.dimension:
            # Truncate
            embedding = embedding[:self.dimension]
            
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
            
        return embedding
        
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            Matrix of embeddings (n_texts, dimension)
        """
        embeddings = np.zeros((len(texts), self.dimension), dtype=np.float32)
        
        for i, text in enumerate(texts):
            embeddings[i] = self.embed(text)
            
        return embeddings
        
    def get_vocabulary_stats(self) -> Dict[str, any]:
        """
        Get statistics about the fitted vocabulary.
        
        Returns:
            Dictionary with vocabulary statistics
        """
        if not self._is_fitted:
            return {"fitted": False}
            
        return {
            "fitted": True,
            "vocabulary_size": len(self._vocabulary),
            "dimension": self.dimension,
            "max_features": self.max_features,
            "stopwords_count": len(self._stopwords),
            "uses_svd": self._svd_components is not None,
        }