"""
Test configuration and fixtures for KB Playground tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from kb_playground import KnowledgeBase, Document


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def kb(temp_dir):
    """Create a knowledge base instance for testing."""
    return KnowledgeBase(
        dimension=128,  # Smaller dimension for faster tests
        data_dir=str(temp_dir / "kb_data"),
        enable_dvc=False  # Disable DVC for unit tests
    )


@pytest.fixture
def sample_documents():
    """Sample documents for testing."""
    return [
        Document(
            content="Python is a high-level programming language known for its simplicity and readability.",
            title="Python Programming",
            metadata={"category": "programming", "difficulty": "beginner"}
        ),
        Document(
            content="Machine learning is a subset of artificial intelligence that enables computers to learn without explicit programming.",
            title="Machine Learning Basics",
            metadata={"category": "ai", "difficulty": "intermediate"}
        ),
        Document(
            content="Neural networks are computing systems inspired by biological neural networks that constitute animal brains.",
            title="Neural Networks",
            metadata={"category": "ai", "difficulty": "advanced"}
        ),
        Document(
            content="Data structures are ways of organizing and storing data in a computer so that it can be accessed and modified efficiently.",
            title="Data Structures",
            metadata={"category": "programming", "difficulty": "intermediate"}
        ),
        Document(
            content="Algorithms are step-by-step procedures for calculations, data processing, and automated reasoning tasks.",
            title="Algorithms",
            metadata={"category": "programming", "difficulty": "intermediate"}
        )
    ]


@pytest.fixture
def populated_kb(kb, sample_documents):
    """Knowledge base populated with sample documents."""
    kb.add(*sample_documents)
    return kb