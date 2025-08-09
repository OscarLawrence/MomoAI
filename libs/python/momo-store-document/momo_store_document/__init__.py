"""
Momo Store Document

A modular document store implementation for the Momo AI knowledge base.
Provides unified interface for storing and retrieving documents using various backends.
"""

__version__ = "0.1.0"

from .PandasDocumentStore import PandasDocumentBackend
from .main import BaseDocumentBackend, DocumentBackend
from .persistence import PersistenceStrategy, NoPersistence
from .exceptions import KnowledgeBaseError, DocumentNotFoundError

__all__ = [
    "PandasDocumentBackend",
    "BaseDocumentBackend",
    "DocumentBackend",
    "PersistenceStrategy",
    "NoPersistence",
    "KnowledgeBaseError",
    "DocumentNotFoundError",
]
