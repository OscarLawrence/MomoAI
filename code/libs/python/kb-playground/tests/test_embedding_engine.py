"""
Test the SimpleEmbeddingEngine component.
"""

import pytest
import numpy as np
from kb_playground.embedding_engine import SimpleEmbeddingEngine


class TestSimpleEmbeddingEngine:
    """Test SimpleEmbeddingEngine functionality."""
    
    @pytest.fixture
    def engine(self):
        """Create an embedding engine for testing."""
        return SimpleEmbeddingEngine(dimension=64, max_features=1000)
        
    @pytest.fixture
    def sample_documents(self):
        """Sample documents for training."""
        return [
            "Python is a programming language used for data science and web development.",
            "Machine learning algorithms can learn patterns from data automatically.",
            "Neural networks are inspired by the structure of the human brain.",
            "Data structures organize information efficiently in computer memory.",
            "Algorithms are step-by-step procedures for solving computational problems.",
            "Software engineering involves designing and maintaining large code bases.",
            "Artificial intelligence aims to create machines that can think and reason.",
            "Database systems store and retrieve information reliably and efficiently."
        ]
        
    def test_initialization(self, engine):
        """Test engine initialization."""
        assert engine.dimension == 64
        assert engine.max_features == 1000
        assert not engine._is_fitted
        assert len(engine._vocabulary) == 0
        
    def test_tokenization(self, engine):
        """Test text tokenization."""
        text = "This is a test document with some words!"
        tokens = engine._tokenize(text)
        
        # Should remove stopwords and short tokens
        assert "this" not in tokens  # stopword
        assert "is" not in tokens    # stopword
        assert "test" in tokens
        assert "document" in tokens
        assert "words" in tokens
        
    def test_fit_on_documents(self, engine, sample_documents):
        """Test fitting the engine on documents."""
        engine.fit(sample_documents)
        
        assert engine._is_fitted
        assert len(engine._vocabulary) > 0
        assert engine._idf_weights is not None
        assert engine._svd_components is not None
        
    def test_fit_empty_documents(self, engine):
        """Test fitting on empty document list."""
        with pytest.raises(ValueError, match="Cannot fit on empty"):
            engine.fit([])
            
    def test_embed_before_fitting(self, engine):
        """Test embedding before fitting raises error."""
        with pytest.raises(RuntimeError, match="must be fitted"):
            engine.embed("test text")
            
    def test_embed_single_text(self, engine, sample_documents):
        """Test embedding a single text."""
        engine.fit(sample_documents)
        
        text = "Python programming language"
        embedding = engine.embed(text)
        
        assert embedding.shape == (64,)
        assert np.isclose(np.linalg.norm(embedding), 1.0, atol=1e-6)  # Normalized
        
    def test_embed_batch(self, engine, sample_documents):
        """Test embedding multiple texts."""
        engine.fit(sample_documents)
        
        test_texts = [
            "Python programming",
            "Machine learning algorithms", 
            "Neural network architecture"
        ]
        
        embeddings = engine.embed_batch(test_texts)
        
        assert embeddings.shape == (3, 64)
        
        # Check each embedding is normalized
        for i in range(3):
            norm = np.linalg.norm(embeddings[i])
            assert np.isclose(norm, 1.0, atol=1e-6)
            
    def test_embedding_similarity(self, engine, sample_documents):
        """Test that similar texts have similar embeddings."""
        engine.fit(sample_documents)
        
        # Similar texts
        text1 = "Python programming language"
        text2 = "Python programming code"
        
        # Dissimilar text
        text3 = "Neural network architecture"
        
        emb1 = engine.embed(text1)
        emb2 = engine.embed(text2)
        emb3 = engine.embed(text3)
        
        # Similar texts should have higher similarity
        sim_12 = np.dot(emb1, emb2)
        sim_13 = np.dot(emb1, emb3)
        
        assert sim_12 > sim_13
        
    def test_embedding_deterministic(self, engine, sample_documents):
        """Test that embeddings are deterministic."""
        engine.fit(sample_documents)
        
        text = "Test document for determinism"
        
        emb1 = engine.embed(text)
        emb2 = engine.embed(text)
        
        np.testing.assert_array_equal(emb1, emb2)
        
    def test_vocabulary_stats(self, engine, sample_documents):
        """Test vocabulary statistics."""
        # Before fitting
        stats = engine.get_vocabulary_stats()
        assert not stats["fitted"]
        
        # After fitting
        engine.fit(sample_documents)
        stats = engine.get_vocabulary_stats()
        
        assert stats["fitted"]
        assert stats["vocabulary_size"] > 0
        assert stats["dimension"] == 64
        assert stats["max_features"] == 1000
        assert isinstance(stats["uses_svd"], bool)
        
    def test_small_vocabulary(self):
        """Test engine with vocabulary smaller than target dimension."""
        engine = SimpleEmbeddingEngine(dimension=100, max_features=50)
        
        # Use documents with limited vocabulary
        docs = ["cat dog", "dog bird", "bird cat"]
        engine.fit(docs)
        
        embedding = engine.embed("cat")
        assert embedding.shape == (100,)
        
    def test_large_vocabulary(self):
        """Test engine with vocabulary larger than target dimension."""
        engine = SimpleEmbeddingEngine(dimension=10, max_features=1000)
        
        # Create documents with many unique words
        docs = [f"word{i} text{i} document{i}" for i in range(100)]
        engine.fit(docs)
        
        embedding = engine.embed("word1 text1")
        assert embedding.shape == (10,)
        
    def test_empty_text_embedding(self, engine, sample_documents):
        """Test embedding empty or whitespace-only text."""
        engine.fit(sample_documents)
        
        # Empty text
        emb_empty = engine.embed("")
        assert emb_empty.shape == (64,)
        
        # Whitespace only
        emb_whitespace = engine.embed("   \n\t  ")
        assert emb_whitespace.shape == (64,)
        
    def test_stopword_filtering(self, engine):
        """Test that stopwords are properly filtered."""
        docs = ["the quick brown fox", "a fast brown animal"]
        engine.fit(docs)
        
        # Stopwords should not be in vocabulary
        assert "the" not in engine._vocabulary
        assert "a" not in engine._vocabulary
        
        # Content words should be in vocabulary
        assert "quick" in engine._vocabulary or "brown" in engine._vocabulary
        
    def test_case_insensitive(self, engine, sample_documents):
        """Test that processing is case insensitive."""
        engine.fit(sample_documents)
        
        text1 = "Python Programming"
        text2 = "python programming"
        
        emb1 = engine.embed(text1)
        emb2 = engine.embed(text2)
        
        np.testing.assert_array_equal(emb1, emb2)