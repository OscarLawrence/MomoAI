# Python Production Implementation Guide

## Executive Summary

This guide outlines the implementation of a production-grade Python version of the Momo docless knowledge base system, leveraging Python's superior AI/ML ecosystem while maintaining the core architectural principles proven in the TypeScript prototype.

## Why Python for Production

### ✅ **Strategic Advantages**
- **Native AI/ML ecosystem** with mature libraries (spaCy, transformers, chromadb)
- **Better performance** for text processing and ML operations
- **Rich scientific computing** stack (NumPy, SciPy, pandas)
- **Established deployment patterns** for ML systems
- **Superior debugging tools** for complex data processing

### 🎯 **Production Requirements**
- **Performance**: Handle 10,000+ files and 100,000+ entities
- **Scalability**: Support multiple repositories and concurrent users
- **Reliability**: 99.9% uptime with graceful error handling
- **Maintainability**: Clean architecture with comprehensive testing
- **Extensibility**: Plugin system for custom extractors and processors

## Architecture Overview

### Core Components

```
momo-python/
├── momo/
│   ├── core/                 # Core system components
│   │   ├── knowledge_base.py # Main KB interface
│   │   ├── embeddings.py     # Embedding strategies
│   │   ├── extractors.py     # Code entity extraction
│   │   └── storage.py        # Persistence layer
│   ├── agents/               # Agent framework
│   │   ├── base_agent.py     # Foundation agent class
│   │   ├── registry.py       # Agent discovery
│   │   └── orchestrator.py   # Task coordination
│   ├── cli/                  # Command-line interface
│   │   ├── commands/         # CLI command modules
│   │   └── main.py          # Entry point
│   ├── api/                  # REST API (optional)
│   │   ├── routes/          # API endpoints
│   │   └── server.py        # FastAPI server
│   └── utils/               # Shared utilities
├── tests/                   # Comprehensive test suite
├── docs/                    # Generated documentation
├── scripts/                 # Deployment and maintenance
└── pyproject.toml          # Modern Python packaging
```

## Phase 1: Foundation (Weeks 1-2)

### 1.1 Project Setup

**Modern Python Packaging**
```toml
# pyproject.toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "momo-kb"
version = "0.1.0"
description = "Docless knowledge base for AI-enhanced development"
authors = [{name = "Your Name", email = "your.email@example.com"}]
dependencies = [
    "spacy>=3.7.0",
    "sentence-transformers>=2.2.0",
    "chromadb>=0.4.0",
    "pydantic>=2.0.0",
    "typer>=0.9.0",
    "rich>=13.0.0",
    "asyncio-mqtt>=0.13.0",
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
    "pre-commit>=3.5.0",
]

[project.scripts]
momo = "momo.cli.main:app"
```

**Development Environment**
```bash
# Setup script
#!/bin/bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pre-commit install
python -m spacy download en_core_web_sm
```

### 1.2 Core Data Models

**Knowledge Base Types**
```python
# momo/core/types.py
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field
import uuid

class KnowledgeType(str, Enum):
    CODE = "code"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    TEST = "test"

class EntityType(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    INTERFACE = "interface"
    VARIABLE = "variable"
    IMPORT = "import"
    EXPORT = "export"

class Relation(BaseModel):
    type: str
    target_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class KnowledgeEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: KnowledgeType
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    relations: List[Relation] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class QueryRequest(BaseModel):
    query: str
    max_results: int = 10
    filters: Dict[str, Any] = Field(default_factory=dict)
    include_metadata: bool = True

class QueryResponse(BaseModel):
    results: List[KnowledgeEntry]
    total_count: int
    retrieval_time_ms: float
    relevance_scores: List[float]
```

### 1.3 Storage Layer

**Abstract Storage Interface**
```python
# momo/core/storage.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .types import KnowledgeEntry, QueryRequest, QueryResponse

class StorageBackend(ABC):
    """Abstract base class for storage backends"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the storage backend"""
        pass
    
    @abstractmethod
    async def store(self, entry: KnowledgeEntry) -> None:
        """Store a knowledge entry"""
        pass
    
    @abstractmethod
    async def retrieve(self, entry_id: str) -> Optional[KnowledgeEntry]:
        """Retrieve a knowledge entry by ID"""
        pass
    
    @abstractmethod
    async def query(self, request: QueryRequest) -> QueryResponse:
        """Query knowledge entries"""
        pass
    
    @abstractmethod
    async def update(self, entry_id: str, updates: Dict[str, Any]) -> None:
        """Update a knowledge entry"""
        pass
    
    @abstractmethod
    async def delete(self, entry_id: str) -> None:
        """Delete a knowledge entry"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        pass
```

## Phase 2: Core Implementation (Weeks 3-4)

### 2.1 Embedding Strategies

**Multi-Strategy Embedding System**
```python
# momo/core/embeddings.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy

class EmbeddingStrategy(ABC):
    """Abstract base class for embedding strategies"""
    
    @abstractmethod
    async def encode(self, texts: List[str]) -> np.ndarray:
        """Encode texts into embeddings"""
        pass
    
    @abstractmethod
    async def similarity(self, query_embedding: np.ndarray, 
                        doc_embeddings: np.ndarray) -> np.ndarray:
        """Compute similarity scores"""
        pass

class TFIDFEmbedding(EmbeddingStrategy):
    """TF-IDF based embeddings for fast local search"""
    
    def __init__(self, max_features: int = 10000):
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8
        )
        self.fitted = False
    
    async def encode(self, texts: List[str]) -> np.ndarray:
        if not self.fitted:
            embeddings = self.vectorizer.fit_transform(texts)
            self.fitted = True
        else:
            embeddings = self.vectorizer.transform(texts)
        return embeddings.toarray()
    
    async def similarity(self, query_embedding: np.ndarray, 
                        doc_embeddings: np.ndarray) -> np.ndarray:
        # Cosine similarity
        query_norm = np.linalg.norm(query_embedding)
        doc_norms = np.linalg.norm(doc_embeddings, axis=1)
        
        similarities = np.dot(doc_embeddings, query_embedding) / (doc_norms * query_norm)
        return similarities

class TransformerEmbedding(EmbeddingStrategy):
    """Transformer-based embeddings for semantic search"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
    
    async def encode(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts, convert_to_numpy=True)
    
    async def similarity(self, query_embedding: np.ndarray, 
                        doc_embeddings: np.ndarray) -> np.ndarray:
        from sentence_transformers.util import cos_sim
        similarities = cos_sim(query_embedding, doc_embeddings)
        return similarities.numpy().flatten()

class HybridEmbedding(EmbeddingStrategy):
    """Hybrid approach combining TF-IDF and transformer embeddings"""
    
    def __init__(self, tfidf_weight: float = 0.3, transformer_weight: float = 0.7):
        self.tfidf = TFIDFEmbedding()
        self.transformer = TransformerEmbedding()
        self.tfidf_weight = tfidf_weight
        self.transformer_weight = transformer_weight
    
    async def encode(self, texts: List[str]) -> Dict[str, np.ndarray]:
        tfidf_embeddings = await self.tfidf.encode(texts)
        transformer_embeddings = await self.transformer.encode(texts)
        
        return {
            'tfidf': tfidf_embeddings,
            'transformer': transformer_embeddings
        }
    
    async def similarity(self, query_embeddings: Dict[str, np.ndarray], 
                        doc_embeddings: Dict[str, np.ndarray]) -> np.ndarray:
        tfidf_sim = await self.tfidf.similarity(
            query_embeddings['tfidf'], doc_embeddings['tfidf']
        )
        transformer_sim = await self.transformer.similarity(
            query_embeddings['transformer'], doc_embeddings['transformer']
        )
        
        # Weighted combination
        combined_sim = (self.tfidf_weight * tfidf_sim + 
                       self.transformer_weight * transformer_sim)
        return combined_sim
```

### 2.2 Advanced Code Extraction

**Multi-Language AST-Based Extraction**
```python
# momo/core/extractors.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import ast
import re
from pathlib import Path
import spacy
from tree_sitter import Language, Parser
from .types import KnowledgeEntry, KnowledgeType, EntityType

class CodeExtractor(ABC):
    """Abstract base class for code extractors"""
    
    @abstractmethod
    async def extract(self, file_path: Path, content: str) -> List[KnowledgeEntry]:
        """Extract knowledge entries from source code"""
        pass

class PythonASTExtractor(CodeExtractor):
    """Python AST-based extractor for precise code analysis"""
    
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
    
    async def extract(self, file_path: Path, content: str) -> List[KnowledgeEntry]:
        entries = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    entries.append(await self._extract_function(node, file_path, content))
                elif isinstance(node, ast.ClassDef):
                    entries.append(await self._extract_class(node, file_path, content))
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    entries.append(await self._extract_import(node, file_path))
        
        except SyntaxError as e:
            # Log error but continue processing
            print(f"Syntax error in {file_path}: {e}")
        
        return [e for e in entries if e is not None]
    
    async def _extract_function(self, node: ast.FunctionDef, 
                               file_path: Path, content: str) -> KnowledgeEntry:
        # Extract function signature
        signature = self._get_function_signature(node)
        
        # Extract docstring
        docstring = ast.get_docstring(node) or ""
        
        # Extract decorators
        decorators = [self._get_decorator_name(d) for d in node.decorator_list]
        
        # Get line numbers
        start_line = node.lineno
        end_line = node.end_lineno or start_line
        
        # Extract function body for context
        lines = content.split('\n')
        function_content = '\n'.join(lines[start_line-1:end_line])
        
        return KnowledgeEntry(
            id=f"{file_path}:{node.name}:function:{start_line}",
            type=KnowledgeType.CODE,
            content=function_content,
            metadata={
                "entity_name": node.name,
                "entity_type": EntityType.FUNCTION,
                "file_path": str(file_path),
                "start_line": start_line,
                "end_line": end_line,
                "signature": signature,
                "docstring": docstring,
                "decorators": decorators,
                "parameters": self._extract_parameters(node),
                "return_annotation": self._get_return_annotation(node),
                "complexity": self._calculate_complexity(node),
                "language": "python"
            }
        )
    
    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Extract function signature"""
        args = []
        
        # Regular arguments
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)
        
        # *args
        if node.args.vararg:
            vararg = f"*{node.args.vararg.arg}"
            if node.args.vararg.annotation:
                vararg += f": {ast.unparse(node.args.vararg.annotation)}"
            args.append(vararg)
        
        # **kwargs
        if node.args.kwarg:
            kwarg = f"**{node.args.kwarg.arg}"
            if node.args.kwarg.annotation:
                kwarg += f": {ast.unparse(node.args.kwarg.annotation)}"
            args.append(kwarg)
        
        signature = f"{node.name}({', '.join(args)})"
        
        # Return annotation
        if node.returns:
            signature += f" -> {ast.unparse(node.returns)}"
        
        return signature
    
    def _extract_parameters(self, node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """Extract parameter information"""
        params = []
        for arg in node.args.args:
            param_info = {
                "name": arg.arg,
                "type": ast.unparse(arg.annotation) if arg.annotation else None,
                "default": None
            }
            params.append(param_info)
        return params
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

class TypeScriptTreeSitterExtractor(CodeExtractor):
    """TypeScript extractor using Tree-sitter for accurate parsing"""
    
    def __init__(self):
        # Initialize Tree-sitter parser for TypeScript
        self.parser = Parser()
        # Note: You'll need to build tree-sitter-typescript
        # Language.build_library('build/languages.so', ['tree-sitter-typescript'])
        # TS_LANGUAGE = Language('build/languages.so', 'typescript')
        # self.parser.set_language(TS_LANGUAGE)
    
    async def extract(self, file_path: Path, content: str) -> List[KnowledgeEntry]:
        # Implementation for TypeScript extraction
        # This would use Tree-sitter to parse TypeScript/JavaScript
        pass

## Phase 3: Knowledge Base Core (Weeks 5-6)

### 3.1 Main Knowledge Base Implementation

```python
# momo/core/knowledge_base.py
import asyncio
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import aiofiles
import json
from datetime import datetime
import logging

from .types import KnowledgeEntry, QueryRequest, QueryResponse, KnowledgeType
from .storage import StorageBackend
from .embeddings import EmbeddingStrategy, HybridEmbedding
from .extractors import CodeExtractor, PythonASTExtractor

logger = logging.getLogger(__name__)

class KnowledgeBase:
    """Main knowledge base implementation with async support"""
    
    def __init__(self, 
                 storage: StorageBackend,
                 embedding_strategy: EmbeddingStrategy = None,
                 extractors: Dict[str, CodeExtractor] = None):
        self.storage = storage
        self.embedding_strategy = embedding_strategy or HybridEmbedding()
        self.extractors = extractors or {
            '.py': PythonASTExtractor(),
            # Add more extractors as needed
        }
        self.initialized = False
    
    async def initialize(self) -> None:
        """Initialize the knowledge base"""
        if self.initialized:
            return
        
        await self.storage.initialize()
        logger.info("Knowledge base initialized")
        self.initialized = True
    
    async def ingest_file(self, file_path: Path) -> List[KnowledgeEntry]:
        """Ingest a single file into the knowledge base"""
        if not self.initialized:
            await self.initialize()
        
        suffix = file_path.suffix.lower()
        extractor = self.extractors.get(suffix)
        
        if not extractor:
            logger.warning(f"No extractor available for {suffix} files")
            return []
        
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            entries = await extractor.extract(file_path, content)
            
            # Store entries
            for entry in entries:
                await self.storage.store(entry)
            
            logger.info(f"Ingested {len(entries)} entities from {file_path}")
            return entries
            
        except Exception as e:
            logger.error(f"Failed to ingest {file_path}: {e}")
            return []
    
    async def ingest_directory(self, directory: Path, 
                              patterns: List[str] = None,
                              ignore_patterns: List[str] = None) -> Dict[str, Any]:
        """Ingest an entire directory with concurrent processing"""
        if not self.initialized:
            await self.initialize()
        
        patterns = patterns or ['*.py', '*.ts', '*.js', '*.tsx', '*.jsx']
        ignore_patterns = ignore_patterns or [
            '**/node_modules/**', '**/venv/**', '**/.git/**', 
            '**/dist/**', '**/build/**', '**/__pycache__/**'
        ]
        
        # Find all files to process
        files_to_process = []
        for pattern in patterns:
            for file_path in directory.rglob(pattern):
                if not any(file_path.match(ignore) for ignore in ignore_patterns):
                    files_to_process.append(file_path)
        
        logger.info(f"Found {len(files_to_process)} files to process")
        
        # Process files concurrently with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent files
        
        async def process_file_with_semaphore(file_path: Path):
            async with semaphore:
                return await self.ingest_file(file_path)
        
        # Process all files
        start_time = datetime.utcnow()
        results = await asyncio.gather(
            *[process_file_with_semaphore(f) for f in files_to_process],
            return_exceptions=True
        )
        
        # Collect statistics
        total_entities = 0
        successful_files = 0
        failed_files = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_files += 1
                logger.error(f"Failed to process {files_to_process[i]}: {result}")
            else:
                successful_files += 1
                total_entities += len(result)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        stats = {
            "total_files": len(files_to_process),
            "successful_files": successful_files,
            "failed_files": failed_files,
            "total_entities": total_entities,
            "processing_time_seconds": processing_time,
            "entities_per_second": total_entities / processing_time if processing_time > 0 else 0
        }
        
        logger.info(f"Ingestion complete: {stats}")
        return stats
    
    async def query(self, request: QueryRequest) -> QueryResponse:
        """Query the knowledge base"""
        if not self.initialized:
            await self.initialize()
        
        return await self.storage.query(request)
    
    async def store_documentation(self, 
                                 entity_id: str,
                                 content: str,
                                 doc_type: str = "guide",
                                 metadata: Dict[str, Any] = None) -> KnowledgeEntry:
        """Store documentation for a code entity"""
        if not self.initialized:
            await self.initialize()
        
        doc_entry = KnowledgeEntry(
            id=f"doc:{entity_id}:{doc_type}",
            type=KnowledgeType.DOCUMENTATION,
            content=content,
            metadata={
                **(metadata or {}),
                "entity_id": entity_id,
                "documentation_type": doc_type,
                "generated_at": datetime.utcnow().isoformat()
            }
        )
        
        await self.storage.store(doc_entry)
        return doc_entry
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        if not self.initialized:
            await self.initialize()
        
        return await self.storage.get_stats()

### 3.2 ChromaDB Storage Backend

```python
# momo/core/storage/chroma_backend.py
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import json
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..types import KnowledgeEntry, QueryRequest, QueryResponse
from ..storage import StorageBackend

class ChromaDBBackend(StorageBackend):
    """ChromaDB-based storage backend for production use"""
    
    def __init__(self, 
                 persist_directory: str = "./data/chroma",
                 collection_name: str = "momo_knowledge",
                 embedding_function = None):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.embedding_function = embedding_function
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def initialize(self) -> None:
        """Initialize ChromaDB client and collection"""
        def _init_sync():
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_function
                )
            except ValueError:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_function,
                    metadata={"description": "Momo docless knowledge base"}
                )
        
        await asyncio.get_event_loop().run_in_executor(self.executor, _init_sync)
    
    async def store(self, entry: KnowledgeEntry) -> None:
        """Store a knowledge entry in ChromaDB"""
        def _store_sync():
            # Prepare document for ChromaDB
            document = self._create_searchable_content(entry)
            metadata = self._prepare_metadata(entry)
            
            self.collection.upsert(
                ids=[entry.id],
                documents=[document],
                metadatas=[metadata]
            )
        
        await asyncio.get_event_loop().run_in_executor(self.executor, _store_sync)
    
    async def query(self, request: QueryRequest) -> QueryResponse:
        """Query knowledge entries using ChromaDB"""
        start_time = time.time()
        
        def _query_sync():
            # Build where clause from filters
            where_clause = self._build_where_clause(request.filters)
            
            results = self.collection.query(
                query_texts=[request.query],
                n_results=request.max_results,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )
            
            return results
        
        chroma_results = await asyncio.get_event_loop().run_in_executor(
            self.executor, _query_sync
        )
        
        # Convert ChromaDB results to KnowledgeEntry objects
        entries = []
        scores = []
        
        if chroma_results['ids'] and len(chroma_results['ids']) > 0:
            for i, doc_id in enumerate(chroma_results['ids'][0]):
                metadata = chroma_results['metadatas'][0][i]
                document = chroma_results['documents'][0][i]
                distance = chroma_results['distances'][0][i]
                
                # Reconstruct KnowledgeEntry
                entry = self._reconstruct_entry(doc_id, document, metadata)
                entries.append(entry)
                
                # Convert distance to similarity score (0-1, higher is better)
                similarity = max(0, 1 - distance)
                scores.append(similarity)
        
        retrieval_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return QueryResponse(
            results=entries,
            total_count=len(entries),
            retrieval_time_ms=retrieval_time,
            relevance_scores=scores
        )
    
    def _create_searchable_content(self, entry: KnowledgeEntry) -> str:
        """Create searchable content from knowledge entry"""
        parts = [entry.content]
        
        # Add metadata fields that should be searchable
        if entry.metadata.get('entity_name'):
            parts.append(entry.metadata['entity_name'])
        if entry.metadata.get('file_path'):
            parts.append(entry.metadata['file_path'])
        if entry.metadata.get('docstring'):
            parts.append(entry.metadata['docstring'])
        if entry.metadata.get('tags'):
            parts.extend(entry.metadata['tags'])
        
        return ' '.join(filter(None, parts))
    
    def _prepare_metadata(self, entry: KnowledgeEntry) -> Dict[str, Any]:
        """Prepare metadata for ChromaDB storage"""
        # ChromaDB has limitations on metadata types
        metadata = {
            "type": entry.type.value,
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat(),
        }
        
        # Add safe metadata fields
        safe_fields = ['entity_name', 'entity_type', 'file_path', 'language', 'start_line']
        for field in safe_fields:
            if field in entry.metadata:
                value = entry.metadata[field]
                # Ensure value is JSON serializable
                if isinstance(value, (str, int, float, bool)):
                    metadata[field] = value
                else:
                    metadata[field] = str(value)
        
        # Store full entry as JSON string for reconstruction
        metadata['_full_entry'] = json.dumps(entry.dict(), default=str)
        
        return metadata

## Phase 4: CLI and API (Weeks 7-8)

### 4.1 Modern CLI with Typer

```python
# momo/cli/main.py
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
import asyncio
from typing import Optional, List

from ..core.knowledge_base import KnowledgeBase
from ..core.storage.chroma_backend import ChromaDBBackend
from ..core.types import QueryRequest

app = typer.Typer(name="momo", help="Momo Docless Knowledge Base CLI")
console = Console()

@app.command()
def ingest(
    path: Path = typer.Argument(..., help="Path to ingest (file or directory)"),
    patterns: Optional[List[str]] = typer.Option(None, "--pattern", "-p", help="File patterns to include"),
    ignore: Optional[List[str]] = typer.Option(None, "--ignore", "-i", help="Patterns to ignore"),
    storage_path: str = typer.Option("./data/chroma", "--storage", "-s", help="Storage directory"),
    collection: str = typer.Option("momo_knowledge", "--collection", "-c", help="Collection name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    """Ingest files into the knowledge base"""
    
    async def _ingest():
        # Initialize knowledge base
        storage = ChromaDBBackend(persist_directory=storage_path, collection_name=collection)
        kb = KnowledgeBase(storage=storage)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing knowledge base...", total=None)
            await kb.initialize()
            
            if path.is_file():
                progress.update(task, description=f"Processing {path.name}...")
                entries = await kb.ingest_file(path)
                console.print(f"✅ Ingested {len(entries)} entities from {path}")
            else:
                progress.update(task, description="Scanning directory...")
                stats = await kb.ingest_directory(
                    directory=path,
                    patterns=patterns,
                    ignore_patterns=ignore
                )
                
                # Display results
                table = Table(title="Ingestion Results")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("Total Files", str(stats["total_files"]))
                table.add_row("Successful", str(stats["successful_files"]))
                table.add_row("Failed", str(stats["failed_files"]))
                table.add_row("Total Entities", str(stats["total_entities"]))
                table.add_row("Processing Time", f"{stats['processing_time_seconds']:.2f}s")
                table.add_row("Entities/Second", f"{stats['entities_per_second']:.1f}")
                
                console.print(table)
    
    asyncio.run(_ingest())

@app.command()
def query(
    query_text: str = typer.Argument(..., help="Search query"),
    max_results: int = typer.Option(10, "--max", "-n", help="Maximum results"),
    storage_path: str = typer.Option("./data/chroma", "--storage", "-s", help="Storage directory"),
    collection: str = typer.Option("momo_knowledge", "--collection", "-c", help="Collection name"),
    show_content: bool = typer.Option(False, "--content", help="Show full content"),
    filter_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by entity type")
):
    """Query the knowledge base"""
    
    async def _query():
        storage = ChromaDBBackend(persist_directory=storage_path, collection_name=collection)
        kb = KnowledgeBase(storage=storage)
        
        await kb.initialize()
        
        # Build query request
        filters = {}
        if filter_type:
            filters["entity_type"] = filter_type
        
        request = QueryRequest(
            query=query_text,
            max_results=max_results,
            filters=filters
        )
        
        with console.status(f"Searching for: {query_text}"):
            response = await kb.query(request)
        
        if not response.results:
            console.print("❌ No results found")
            return
        
        console.print(f"🔍 Found {len(response.results)} results in {response.retrieval_time_ms:.1f}ms\n")
        
        for i, entry in enumerate(response.results, 1):
            score = response.relevance_scores[i-1] if i-1 < len(response.relevance_scores) else 0
            
            console.print(f"[bold cyan]{i}. {entry.metadata.get('entity_name', 'Unknown')}[/bold cyan]")
            console.print(f"   📁 {entry.metadata.get('file_path', 'Unknown')}")
            console.print(f"   🏷️  {entry.metadata.get('entity_type', 'Unknown')} | Score: {score:.3f}")
            
            if show_content:
                content_preview = entry.content[:200] + "..." if len(entry.content) > 200 else entry.content
                console.print(f"   📝 {content_preview}")
            
            console.print()
    
    asyncio.run(_query())

@app.command()
def stats(
    storage_path: str = typer.Option("./data/chroma", "--storage", "-s", help="Storage directory"),
    collection: str = typer.Option("momo_knowledge", "--collection", "-c", help="Collection name")
):
    """Show knowledge base statistics"""
    
    async def _stats():
        storage = ChromaDBBackend(persist_directory=storage_path, collection_name=collection)
        kb = KnowledgeBase(storage=storage)
        
        await kb.initialize()
        stats = await kb.get_stats()
        
        table = Table(title="Knowledge Base Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in stats.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    table.add_row(f"{key}.{sub_key}", str(sub_value))
            else:
                table.add_row(key, str(value))
        
        console.print(table)
    
    asyncio.run(_stats())

### 4.2 FastAPI REST API

```python
# momo/api/server.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
from contextlib import asynccontextmanager

from ..core.knowledge_base import KnowledgeBase
from ..core.storage.chroma_backend import ChromaDBBackend
from ..core.types import QueryRequest, QueryResponse, KnowledgeEntry

# Global knowledge base instance
kb: Optional[KnowledgeBase] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global kb
    storage = ChromaDBBackend()
    kb = KnowledgeBase(storage=storage)
    await kb.initialize()
    yield
    # Shutdown
    kb = None

app = FastAPI(
    title="Momo Knowledge Base API",
    description="REST API for the Momo docless knowledge base",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequestAPI(BaseModel):
    query: str
    max_results: int = 10
    filters: Dict[str, Any] = {}

class IngestRequest(BaseModel):
    path: str
    patterns: Optional[List[str]] = None
    ignore_patterns: Optional[List[str]] = None

def get_kb() -> KnowledgeBase:
    if kb is None:
        raise HTTPException(status_code=503, detail="Knowledge base not initialized")
    return kb

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "momo-kb"}

@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(
    request: QueryRequestAPI,
    knowledge_base: KnowledgeBase = Depends(get_kb)
):
    """Query the knowledge base"""
    query_req = QueryRequest(
        query=request.query,
        max_results=request.max_results,
        filters=request.filters
    )
    
    return await knowledge_base.query(query_req)

@app.post("/ingest")
async def ingest_path(
    request: IngestRequest,
    knowledge_base: KnowledgeBase = Depends(get_kb)
):
    """Ingest files into the knowledge base"""
    from pathlib import Path
    
    path = Path(request.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Path not found")
    
    if path.is_file():
        entries = await knowledge_base.ingest_file(path)
        return {"message": f"Ingested {len(entries)} entities", "entities": len(entries)}
    else:
        stats = await knowledge_base.ingest_directory(
            directory=path,
            patterns=request.patterns,
            ignore_patterns=request.ignore_patterns
        )
        return {"message": "Directory ingestion complete", "stats": stats}

@app.get("/stats")
async def get_stats(knowledge_base: KnowledgeBase = Depends(get_kb)):
    """Get knowledge base statistics"""
    return await knowledge_base.get_stats()

@app.get("/entries/{entry_id}")
async def get_entry(
    entry_id: str,
    knowledge_base: KnowledgeBase = Depends(get_kb)
):
    """Get a specific knowledge entry"""
    entry = await knowledge_base.storage.retrieve(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry

## Phase 5: Testing Strategy (Week 9)

### 5.1 Comprehensive Test Suite

```python
# tests/conftest.py
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Generator

from momo.core.knowledge_base import KnowledgeBase
from momo.core.storage.chroma_backend import ChromaDBBackend
from momo.core.types import KnowledgeEntry, KnowledgeType

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def temp_storage_dir():
    """Create a temporary directory for testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
async def test_kb(temp_storage_dir):
    """Create a test knowledge base"""
    storage = ChromaDBBackend(persist_directory=temp_storage_dir)
    kb = KnowledgeBase(storage=storage)
    await kb.initialize()
    yield kb

@pytest.fixture
def sample_python_code():
    """Sample Python code for testing"""
    return '''
def calculate_fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number.
    
    Args:
        n: The position in the Fibonacci sequence
        
    Returns:
        The nth Fibonacci number
    """
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

class MathUtils:
    """Utility class for mathematical operations"""
    
    @staticmethod
    def is_prime(num: int) -> bool:
        """Check if a number is prime"""
        if num < 2:
            return False
        for i in range(2, int(num ** 0.5) + 1):
            if num % i == 0:
                return False
        return True
'''

# tests/test_knowledge_base.py
import pytest
from pathlib import Path
import tempfile

from momo.core.types import QueryRequest, KnowledgeType

@pytest.mark.asyncio
async def test_ingest_file(test_kb, sample_python_code):
    """Test file ingestion"""
    # Create temporary Python file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(sample_python_code)
        temp_file = Path(f.name)
    
    try:
        # Ingest the file
        entries = await test_kb.ingest_file(temp_file)
        
        # Verify entities were extracted
        assert len(entries) > 0
        
        # Check for function and class entities
        function_entries = [e for e in entries if e.metadata.get('entity_type') == 'function']
        class_entries = [e for e in entries if e.metadata.get('entity_type') == 'class']
        
        assert len(function_entries) >= 1  # calculate_fibonacci, is_prime
        assert len(class_entries) >= 1     # MathUtils
        
        # Verify metadata
        fib_entry = next((e for e in function_entries if e.metadata.get('entity_name') == 'calculate_fibonacci'), None)
        assert fib_entry is not None
        assert 'docstring' in fib_entry.metadata
        assert 'signature' in fib_entry.metadata
        
    finally:
        temp_file.unlink()

@pytest.mark.asyncio
async def test_query_functionality(test_kb, sample_python_code):
    """Test querying functionality"""
    # First ingest some data
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(sample_python_code)
        temp_file = Path(f.name)
    
    try:
        await test_kb.ingest_file(temp_file)
        
        # Test basic query
        request = QueryRequest(query="fibonacci function", max_results=5)
        response = await test_kb.query(request)
        
        assert len(response.results) > 0
        assert response.retrieval_time_ms > 0
        
        # Check if fibonacci function is in results
        fibonacci_found = any(
            'fibonacci' in entry.metadata.get('entity_name', '').lower()
            for entry in response.results
        )
        assert fibonacci_found
        
    finally:
        temp_file.unlink()

@pytest.mark.asyncio
async def test_documentation_storage(test_kb):
    """Test documentation storage and retrieval"""
    # Store documentation
    doc_entry = await test_kb.store_documentation(
        entity_id="test_function",
        content="This is test documentation for a function",
        doc_type="guide",
        metadata={"author": "test", "version": "1.0"}
    )
    
    assert doc_entry.type == KnowledgeType.DOCUMENTATION
    assert "test_function" in doc_entry.metadata["entity_id"]
    
    # Query for the documentation
    request = QueryRequest(query="test documentation", max_results=5)
    response = await test_kb.query(request)
    
    doc_found = any(
        entry.type == KnowledgeType.DOCUMENTATION
        for entry in response.results
    )
    assert doc_found

### 5.2 Performance Tests

```python
# tests/test_performance.py
import pytest
import time
import asyncio
from pathlib import Path
import tempfile

@pytest.mark.asyncio
async def test_large_file_ingestion_performance(test_kb):
    """Test performance with large files"""
    # Generate a large Python file
    large_code = ""
    for i in range(1000):
        large_code += f'''
def function_{i}(param1: int, param2: str) -> bool:
    """Function number {i} for testing performance"""
    return param1 > len(param2)

class Class_{i}:
    """Class number {i} for testing"""
    
    def method_{i}(self):
        return "method_{i}"
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(large_code)
        temp_file = Path(f.name)
    
    try:
        start_time = time.time()
        entries = await test_kb.ingest_file(temp_file)
        ingestion_time = time.time() - start_time
        
        # Performance assertions
        assert len(entries) >= 2000  # Should extract many entities
        assert ingestion_time < 30   # Should complete within 30 seconds
        
        # Test query performance
        start_time = time.time()
        request = QueryRequest(query="function_500", max_results=10)
        response = await test_kb.query(request)
        query_time = time.time() - start_time
        
        assert query_time < 1.0  # Queries should be fast
        assert len(response.results) > 0
        
    finally:
        temp_file.unlink()

## Phase 6: Deployment & Production (Week 10)

### 6.1 Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .
RUN pip install -e .

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "momo.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  momo-api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./repositories:/app/repositories:ro
    environment:
      - PYTHONPATH=/app
      - LOG_LEVEL=INFO
    restart: unless-stopped
    
  momo-worker:
    build: .
    command: ["python", "-m", "momo.cli.main", "worker"]
    volumes:
      - ./data:/app/data
      - ./repositories:/app/repositories:ro
    environment:
      - PYTHONPATH=/app
      - LOG_LEVEL=INFO
    restart: unless-stopped
    depends_on:
      - momo-api

volumes:
  momo-data:
```

### 6.2 Production Configuration

```python
# momo/config.py
from pydantic import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # Storage settings
    storage_backend: str = "chroma"
    chroma_persist_directory: str = "./data/chroma"
    chroma_collection_name: str = "momo_knowledge"
    
    # Embedding settings
    embedding_strategy: str = "hybrid"  # tfidf, transformer, hybrid
    transformer_model: str = "all-MiniLM-L6-v2"
    
    # Performance settings
    max_concurrent_files: int = 10
    query_timeout_seconds: int = 30
    max_file_size_mb: int = 10
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Security
    api_key: Optional[str] = None
    allowed_origins: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        env_prefix = "MOMO_"

settings = Settings()
```

### 6.3 Monitoring and Observability

```python
# momo/monitoring.py
import time
import logging
from functools import wraps
from typing import Dict, Any
import asyncio
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Metrics
query_counter = Counter('momo_queries_total', 'Total number of queries', ['status'])
query_duration = Histogram('momo_query_duration_seconds', 'Query duration')
ingestion_counter = Counter('momo_ingestions_total', 'Total number of ingestions', ['status'])
knowledge_entries = Gauge('momo_knowledge_entries_total', 'Total knowledge entries')

def monitor_async(metric_name: str):
    """Decorator to monitor async functions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                logging.error(f"Error in {func.__name__}: {e}")
                raise
            finally:
                duration = time.time() - start_time
                
                if metric_name == "query":
                    query_counter.labels(status=status).inc()
                    query_duration.observe(duration)
                elif metric_name == "ingestion":
                    ingestion_counter.labels(status=status).inc()
                
                logging.info(f"{func.__name__} completed in {duration:.2f}s with status {status}")
        
        return wrapper
    return decorator

class HealthChecker:
    """Health check for the knowledge base system"""
    
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
    
    async def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "checks": {}
        }
        
        try:
            # Check storage connectivity
            start_time = time.time()
            stats = await self.kb.get_stats()
            storage_time = time.time() - start_time
            
            health_status["checks"]["storage"] = {
                "status": "healthy",
                "response_time_ms": storage_time * 1000,
                "total_entries": stats.get("total_entries", 0)
            }
            
            # Check query functionality
            start_time = time.time()
            test_query = QueryRequest(query="test", max_results=1)
            await self.kb.query(test_query)
            query_time = time.time() - start_time
            
            health_status["checks"]["query"] = {
                "status": "healthy",
                "response_time_ms": query_time * 1000
            }
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status

def start_metrics_server(port: int = 9090):
    """Start Prometheus metrics server"""
    start_http_server(port)
    logging.info(f"Metrics server started on port {port}")
```

This completes the comprehensive Python production implementation guide. The guide covers all essential aspects from project setup to production deployment with monitoring. Should I now create the migration guide for moving to Go/Rust/C++?
