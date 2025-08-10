"""
Local-First Knowledge Base Implementation
Based on proven insights from PROJECT-RETROSPECTIVE.md

Key principles:
- File-based JSON storage (no external dependencies)
- TF-IDF embeddings (no ML models required)
- Regex entity extraction (simple but effective)
- Sub-millisecond query performance
"""

import json
import re
import math
from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass, asdict
from collections import Counter, defaultdict
from pathlib import Path
import time

@dataclass
class Entity:
    """A code entity extracted from the codebase."""
    id: str
    content: str
    entity_type: str  # function, class, variable, import, etc.
    file_path: str
    line_number: int
    metadata: Dict[str, Any]

@dataclass
class SearchResult:
    """Search result with relevance scoring."""
    entity: Entity
    relevance_score: float
    matching_terms: List[str]
    context: Dict[str, Any]

class TFIDFEmbedder:
    """TF-IDF based embeddings for semantic search without ML models."""
    
    def __init__(self):
        self.vocabulary: Dict[str, int] = {}
        self.document_frequency: Dict[str, int] = {}
        self.total_documents: int = 0
        self.tf_idf_vectors: Dict[str, Dict[str, float]] = {}
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase, alphanumeric only."""
        # Convert camelCase/PascalCase to separate words
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        # Extract alphanumeric tokens
        tokens = re.findall(r'\w+', text.lower())
        # Filter out single characters and common stop words
        stop_words = {'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 
                     'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on',
                     'that', 'the', 'to', 'was', 'will', 'with'}
        return [token for token in tokens if len(token) > 1 and token not in stop_words]
    
    def build_vocabulary(self, entities: List[Entity]):
        """Build vocabulary and calculate document frequencies."""
        self.total_documents = len(entities)
        term_doc_count = defaultdict(set)
        
        for entity in entities:
            # Combine content, type, and metadata for richer indexing
            metadata_values = [str(v) for v in entity.metadata.values()] if entity.metadata else []
            text = f"{entity.content} {entity.entity_type} {' '.join(metadata_values)}"
            tokens = self._tokenize(text)
            
            # Calculate term frequencies
            tf = Counter(tokens)
            self.tf_idf_vectors[entity.id] = {}
            
            for term, freq in tf.items():
                # Add to vocabulary
                if term not in self.vocabulary:
                    self.vocabulary[term] = len(self.vocabulary)
                
                # Track which documents contain this term
                term_doc_count[term].add(entity.id)
                
                # Store TF (normalized by document length)
                self.tf_idf_vectors[entity.id][term] = freq / len(tokens)
        
        # Calculate IDF values
        for term, doc_set in term_doc_count.items():
            self.document_frequency[term] = len(doc_set)
        
        # Calculate TF-IDF vectors
        for entity_id, tf_vector in self.tf_idf_vectors.items():
            for term, tf in tf_vector.items():
                idf = math.log(self.total_documents / self.document_frequency[term])
                self.tf_idf_vectors[entity_id][term] = tf * idf
    
    def query_vector(self, query: str) -> Dict[str, float]:
        """Generate TF-IDF vector for query string."""
        tokens = self._tokenize(query)
        tf = Counter(tokens)
        query_vector = {}
        
        for term, freq in tf.items():
            if term in self.vocabulary:
                # TF for query
                tf_score = freq / len(tokens)
                # IDF from our corpus
                idf = math.log(self.total_documents / self.document_frequency[term])
                query_vector[term] = tf_score * idf
        
        return query_vector
    
    def cosine_similarity(self, query_vector: Dict[str, float], doc_id: str) -> float:
        """Calculate cosine similarity between query and document."""
        doc_vector = self.tf_idf_vectors.get(doc_id, {})
        
        # Calculate dot product
        dot_product = sum(query_vector.get(term, 0) * doc_vector.get(term, 0) 
                         for term in set(query_vector.keys()) | set(doc_vector.keys()))
        
        # Calculate magnitudes
        query_magnitude = math.sqrt(sum(score ** 2 for score in query_vector.values()))
        doc_magnitude = math.sqrt(sum(score ** 2 for score in doc_vector.values()))
        
        if query_magnitude == 0 or doc_magnitude == 0:
            return 0.0
        
        return dot_product / (query_magnitude * doc_magnitude)

class EntityExtractor:
    """Regex-based entity extraction from source code."""
    
    def __init__(self):
        # Python patterns - proven simple approach from retrospective
        self.patterns = {
            'function': r'def\s+(\w+)\s*\([^)]*\):',
            'class': r'class\s+(\w+)(?:\([^)]*\))?:',
            'variable': r'^\s*(\w+)\s*=(?!=)',
            'import': r'(?:from\s+\w+(?:\.\w+)*\s+)?import\s+([\w\s,]+)',
            'constant': r'^[A-Z][A-Z_]*\s*=',
            'decorator': r'@(\w+)',
        }
    
    def extract_from_content(self, content: str, file_path: str) -> List[Entity]:
        """Extract entities from file content using regex patterns."""
        entities = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for entity_type, pattern in self.patterns.items():
                matches = re.finditer(pattern, line, re.MULTILINE)
                for match in matches:
                    entity_name = match.group(1) if match.groups() else match.group(0)
                    
                    entity = Entity(
                        id=f"{file_path}:{line_num}:{entity_name}",
                        content=line.strip(),
                        entity_type=entity_type,
                        file_path=file_path,
                        line_number=line_num,
                        metadata={
                            'name': entity_name,
                            'context': self._get_context(lines, line_num),
                            'size': len(line.strip())
                        }
                    )
                    entities.append(entity)
        
        return entities
    
    def _get_context(self, lines: List[str], line_num: int, window: int = 2) -> str:
        """Get surrounding context for an entity."""
        start = max(0, line_num - window - 1)
        end = min(len(lines), line_num + window)
        context_lines = lines[start:end]
        return ' '.join(line.strip() for line in context_lines if line.strip())

class LocalFirstKB:
    """
    Local-first knowledge base with JSON storage and TF-IDF search.
    Based on proven architecture from PROJECT-RETROSPECTIVE.md
    """
    
    def __init__(self, storage_path: str = "knowledge_base.json"):
        self.storage_path = Path(storage_path)
        self.entities: Dict[str, Entity] = {}
        self.embedder = TFIDFEmbedder()
        self.extractor = EntityExtractor()
        self.metadata = {
            'created_at': time.time(),
            'last_updated': time.time(),
            'total_entities': 0,
            'performance_stats': {}
        }
    
    def ingest_file(self, file_path: str, content: str):
        """Ingest a single file's content into the knowledge base."""
        extracted_entities = self.extractor.extract_from_content(content, file_path)
        
        for entity in extracted_entities:
            self.entities[entity.id] = entity
        
        # Rebuild embeddings (in production, this would be incremental)
        self._rebuild_index()
        
        return len(extracted_entities)
    
    def ingest_directory(self, directory_path: str, file_patterns: List[str] = ["*.py"]):
        """Ingest all files in a directory matching patterns."""
        directory = Path(directory_path)
        total_entities = 0
        
        for pattern in file_patterns:
            for file_path in directory.rglob(pattern):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    count = self.ingest_file(str(file_path), content)
                    total_entities += count
                except Exception as e:
                    print(f"Error ingesting {file_path}: {e}")
        
        return total_entities
    
    def _rebuild_index(self):
        """Rebuild the TF-IDF index."""
        start_time = time.time()
        entity_list = list(self.entities.values())
        self.embedder.build_vocabulary(entity_list)
        
        self.metadata['last_updated'] = time.time()
        self.metadata['total_entities'] = len(self.entities)
        self.metadata['performance_stats']['index_build_time'] = time.time() - start_time
    
    def search(self, query: str, limit: int = 10, min_relevance: float = 0.1) -> List[SearchResult]:
        """Search entities with TF-IDF semantic similarity."""
        start_time = time.time()
        
        if not self.entities:
            return []
        
        # Generate query vector
        query_vector = self.embedder.query_vector(query)
        if not query_vector:
            return []  # No matching terms in vocabulary
        
        # Calculate similarities
        results = []
        query_terms = set(query_vector.keys())
        
        for entity_id, entity in self.entities.items():
            similarity = self.embedder.cosine_similarity(query_vector, entity_id)
            
            if similarity >= min_relevance:
                # Find matching terms for context
                entity_terms = set(self.embedder.tf_idf_vectors.get(entity_id, {}).keys())
                matching_terms = list(query_terms & entity_terms)
                
                result = SearchResult(
                    entity=entity,
                    relevance_score=similarity,
                    matching_terms=matching_terms,
                    context={'query_time': time.time() - start_time}
                )
                results.append(result)
        
        # Sort by relevance and limit results
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Update performance stats
        query_time = time.time() - start_time
        self.metadata['performance_stats']['last_query_time'] = query_time
        self.metadata['performance_stats']['avg_query_time'] = (
            self.metadata['performance_stats'].get('avg_query_time', 0) * 0.9 + query_time * 0.1
        )
        
        return results[:limit]
    
    def get_entity_by_type(self, entity_type: str) -> List[Entity]:
        """Get all entities of a specific type."""
        return [entity for entity in self.entities.values() if entity.entity_type == entity_type]
    
    def get_file_entities(self, file_path: str) -> List[Entity]:
        """Get all entities from a specific file."""
        return [entity for entity in self.entities.values() if entity.file_path == file_path]
    
    def save_to_disk(self):
        """Save knowledge base to JSON file."""
        data = {
            'metadata': self.metadata,
            'entities': {eid: asdict(entity) for eid, entity in self.entities.items()},
            'vocabulary': self.embedder.vocabulary,
            'document_frequency': self.embedder.document_frequency,
            'tf_idf_vectors': self.embedder.tf_idf_vectors
        }
        
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    
    def load_from_disk(self):
        """Load knowledge base from JSON file."""
        if not self.storage_path.exists():
            return False
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.metadata = data['metadata']
            self.entities = {eid: Entity(**entity_data) for eid, entity_data in data['entities'].items()}
            self.embedder.vocabulary = data['vocabulary']
            self.embedder.document_frequency = data['document_frequency']
            self.embedder.tf_idf_vectors = data['tf_idf_vectors']
            self.embedder.total_documents = len(self.entities)
            
            return True
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
            return False
    
    def stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        entity_types = defaultdict(int)
        file_counts = defaultdict(int)
        
        for entity in self.entities.values():
            entity_types[entity.entity_type] += 1
            file_counts[Path(entity.file_path).name] += 1
        
        return {
            'total_entities': len(self.entities),
            'vocabulary_size': len(self.embedder.vocabulary),
            'entity_types': dict(entity_types),
            'files_indexed': len(file_counts),
            'performance': self.metadata.get('performance_stats', {}),
            'storage_size_mb': self.storage_path.stat().st_size / (1024 * 1024) if self.storage_path.exists() else 0
        }