"""
Enhanced Local-First Knowledge Base
Incorporates lessons from testing and adds advanced features while maintaining simplicity.

Key improvements:
- Incremental indexing for large codebases
- Enhanced entity extraction with context
- Query optimization and caching
- Better multi-agent integration
- Relationship extraction and graph features
"""

import json
import re
import math
import hashlib
from typing import Dict, List, Set, Tuple, Any, Optional, Iterator
from dataclasses import dataclass, asdict, field
from collections import Counter, defaultdict
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor
import threading

@dataclass
class Entity:
    """Enhanced entity with relationship support."""
    id: str
    content: str
    entity_type: str
    file_path: str
    line_number: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    relationships: List[str] = field(default_factory=list)  # Related entity IDs
    content_hash: str = ""
    
    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.md5(self.content.encode()).hexdigest()

@dataclass
class SearchResult:
    """Enhanced search result with explanation."""
    entity: Entity
    relevance_score: float
    matching_terms: List[str]
    context: Dict[str, Any]
    explanation: str = ""

@dataclass
class Relationship:
    """Represents a relationship between entities."""
    source_id: str
    target_id: str
    relationship_type: str
    strength: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class EnhancedTFIDF:
    """Enhanced TF-IDF with caching and optimization."""
    
    def __init__(self):
        self.vocabulary: Dict[str, int] = {}
        self.document_frequency: Dict[str, int] = {}
        self.total_documents: int = 0
        self.tf_idf_vectors: Dict[str, Dict[str, float]] = {}
        self.query_cache: Dict[str, Dict[str, float]] = {}
        self.cache_lock = threading.RLock()
    
    def _tokenize(self, text: str) -> List[str]:
        """Enhanced tokenization with code-aware features."""
        # Handle camelCase, PascalCase, snake_case
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        text = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', text)
        text = re.sub(r'_', ' ', text)
        
        # Extract alphanumeric tokens, preserve some symbols
        tokens = re.findall(r'\w+|[<>=!]+', text.lower())
        
        # Enhanced stop words for code
        stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'if', 'or', 'not', 'but', 'this',
            'self', 'def', 'class', 'return', 'import', 'from', 'as'
        }
        
        # Filter tokens
        filtered_tokens = []
        for token in tokens:
            if len(token) > 1 and token not in stop_words:
                filtered_tokens.append(token)
                # Add partial matches for compound words
                if len(token) > 6:
                    for i in range(2, len(token)-1):
                        if token[i:i+4] not in stop_words:
                            filtered_tokens.append(token[i:i+4])
        
        return filtered_tokens
    
    def build_vocabulary(self, entities: List[Entity], incremental: bool = False):
        """Build vocabulary with optional incremental updates."""
        if not incremental:
            self.vocabulary.clear()
            self.document_frequency.clear()
            self.tf_idf_vectors.clear()
            self.query_cache.clear()
        
        # Track which documents contain which terms
        term_doc_count = defaultdict(set)
        new_entities = []
        
        for entity in entities:
            # Skip if already processed (incremental mode)
            if incremental and entity.id in self.tf_idf_vectors:
                continue
            
            new_entities.append(entity)
            
            # Enhanced text combining - include relationships
            metadata_values = [str(v) for v in entity.metadata.values()] if entity.metadata else []
            relationship_context = ' '.join(entity.relationships) if entity.relationships else ''
            text = f"{entity.content} {entity.entity_type} {' '.join(metadata_values)} {relationship_context}"
            
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
        
        # Update total documents
        if not incremental:
            self.total_documents = len(entities)
        else:
            self.total_documents = len(self.tf_idf_vectors)
        
        # Update document frequencies (full recalculation for now)
        for term, doc_set in term_doc_count.items():
            self.document_frequency[term] = len(doc_set)
        
        # Calculate TF-IDF vectors for new entities
        for entity in new_entities:
            for term, tf in self.tf_idf_vectors[entity.id].items():
                idf = math.log(self.total_documents / self.document_frequency[term])
                self.tf_idf_vectors[entity.id][term] = tf * idf
    
    def query_vector(self, query: str) -> Dict[str, float]:
        """Generate cached query vector."""
        query_key = query.lower().strip()
        
        with self.cache_lock:
            if query_key in self.query_cache:
                return self.query_cache[query_key]
        
        tokens = self._tokenize(query)
        tf = Counter(tokens)
        query_vector = {}
        
        for term, freq in tf.items():
            if term in self.vocabulary:
                tf_score = freq / len(tokens)
                idf = math.log(self.total_documents / self.document_frequency[term])
                query_vector[term] = tf_score * idf
        
        # Cache the result
        with self.cache_lock:
            self.query_cache[query_key] = query_vector
            # Limit cache size
            if len(self.query_cache) > 1000:
                # Remove oldest 10% of cache
                old_keys = list(self.query_cache.keys())[:100]
                for key in old_keys:
                    del self.query_cache[key]
        
        return query_vector
    
    def cosine_similarity(self, query_vector: Dict[str, float], doc_id: str) -> float:
        """Calculate cosine similarity with optimizations."""
        doc_vector = self.tf_idf_vectors.get(doc_id, {})
        
        # Quick exit for empty vectors
        if not query_vector or not doc_vector:
            return 0.0
        
        # Only calculate for intersecting terms (optimization)
        common_terms = set(query_vector.keys()) & set(doc_vector.keys())
        if not common_terms:
            return 0.0
        
        # Calculate dot product only for common terms
        dot_product = sum(query_vector[term] * doc_vector[term] for term in common_terms)
        
        # Calculate magnitudes
        query_magnitude = math.sqrt(sum(score ** 2 for score in query_vector.values()))
        doc_magnitude = math.sqrt(sum(score ** 2 for score in doc_vector.values()))
        
        if query_magnitude == 0 or doc_magnitude == 0:
            return 0.0
        
        return dot_product / (query_magnitude * doc_magnitude)

class AdvancedEntityExtractor:
    """Enhanced entity extractor with relationship detection."""
    
    def __init__(self):
        # Enhanced patterns with more context
        self.patterns = {
            'function': r'def\s+(\w+)\s*\([^)]*\):',
            'class': r'class\s+(\w+)(?:\([^)]*\))?:',
            'variable': r'^\s*(\w+)\s*=(?!=)',
            'import': r'(?:from\s+([\w.]+)\s+)?import\s+([\w\s,.*]+)',
            'constant': r'^([A-Z][A-Z_]*)\s*=',
            'decorator': r'@(\w+)',
            'property': r'@property\s+def\s+(\w+)',
            'method': r'def\s+(\w+)\s*\(self',
            'async_function': r'async\s+def\s+(\w+)',
            'type_hint': r':\s*([\w\[\], ]+)\s*(?:=|->)',
        }
        
        # Relationship patterns
        self.relationship_patterns = {
            'inherits': r'class\s+\w+\s*\(([^)]+)\)',
            'calls': r'(\w+)\s*\([^)]*\)',
            'imports': r'from\s+([\w.]+)\s+import|import\s+([\w.]+)',
            'assigns': r'(\w+)\s*=\s*(\w+)',
        }
    
    def extract_from_content(self, content: str, file_path: str) -> Tuple[List[Entity], List[Relationship]]:
        """Extract entities and relationships from content."""
        entities = []
        relationships = []
        lines = content.split('\n')
        
        # First pass: extract entities
        for line_num, line in enumerate(lines, 1):
            for entity_type, pattern in self.patterns.items():
                matches = re.finditer(pattern, line, re.MULTILINE)
                for match in matches:
                    entity_name = self._extract_name(match, entity_type)
                    if entity_name:
                        entity = Entity(
                            id=f"{file_path}:{line_num}:{entity_name}",
                            content=line.strip(),
                            entity_type=entity_type,
                            file_path=file_path,
                            line_number=line_num,
                            metadata={
                                'name': entity_name,
                                'context': self._get_enhanced_context(lines, line_num),
                                'size': len(line.strip()),
                                'complexity': self._estimate_complexity(line),
                                'scope': self._detect_scope(lines, line_num)
                            }
                        )
                        entities.append(entity)
        
        # Second pass: extract relationships
        entity_names = {e.metadata['name']: e.id for e in entities}
        
        for line_num, line in enumerate(lines, 1):
            line_entities = [e for e in entities if e.line_number == line_num]
            
            for rel_type, pattern in self.relationship_patterns.items():
                matches = re.finditer(pattern, line)
                for match in matches:
                    source_entities = line_entities
                    targets = self._extract_relationship_targets(match, rel_type)
                    
                    for source_entity in source_entities:
                        for target in targets:
                            if target in entity_names and target != source_entity.metadata['name']:
                                relationship = Relationship(
                                    source_id=source_entity.id,
                                    target_id=entity_names[target],
                                    relationship_type=rel_type,
                                    strength=self._calculate_relationship_strength(rel_type, line),
                                    metadata={'line': line_num, 'context': line.strip()}
                                )
                                relationships.append(relationship)
        
        return entities, relationships
    
    def _extract_name(self, match, entity_type: str) -> Optional[str]:
        """Extract entity name from regex match."""
        if entity_type == 'import':
            # Handle complex import statements
            groups = match.groups()
            if len(groups) >= 2 and groups[1]:
                return groups[1].split(',')[0].strip()
            elif groups[0]:
                return groups[0]
        elif match.groups():
            return match.group(1)
        return match.group(0) if match.group(0) else None
    
    def _get_enhanced_context(self, lines: List[str], line_num: int, window: int = 3) -> str:
        """Get enhanced context including docstrings and comments."""
        start = max(0, line_num - window - 1)
        end = min(len(lines), line_num + window)
        
        context_lines = []
        for i in range(start, end):
            line = lines[i].strip()
            if line and not line.startswith('#'):  # Exclude comment-only lines
                context_lines.append(line)
        
        return ' '.join(context_lines)
    
    def _estimate_complexity(self, line: str) -> int:
        """Simple complexity estimation."""
        complexity_indicators = ['if', 'for', 'while', 'try', 'except', 'with', 'async', 'await']
        return sum(1 for indicator in complexity_indicators if indicator in line.lower())
    
    def _detect_scope(self, lines: List[str], line_num: int) -> str:
        """Detect if entity is at module, class, or function scope."""
        # Look backwards to find containing scope
        for i in range(line_num - 2, -1, -1):
            line = lines[i].strip()
            if line.startswith('class '):
                return 'class'
            elif line.startswith('def '):
                return 'function'
        return 'module'
    
    def _extract_relationship_targets(self, match, rel_type: str) -> List[str]:
        """Extract target names from relationship matches."""
        if rel_type == 'inherits':
            # Parse inheritance list
            inheritance_str = match.group(1)
            return [name.strip() for name in inheritance_str.split(',')]
        elif rel_type == 'calls':
            return [match.group(1)]
        elif rel_type == 'imports':
            groups = match.groups()
            if groups[0]:
                return [groups[0]]
            elif groups[1]:
                return [groups[1]]
        elif rel_type == 'assigns':
            return [match.group(2)]
        return []
    
    def _calculate_relationship_strength(self, rel_type: str, line: str) -> float:
        """Calculate relationship strength based on type and context."""
        base_strengths = {
            'inherits': 0.9,
            'calls': 0.7,
            'imports': 0.6,
            'assigns': 0.5
        }
        
        base = base_strengths.get(rel_type, 0.5)
        
        # Adjust based on line characteristics
        if 'self.' in line:
            base += 0.1  # Stronger for instance methods
        if line.count('(') > 1:
            base += 0.05  # Stronger for nested calls
        
        return min(base, 1.0)

class EnhancedLocalKB:
    """
    Enhanced local-first knowledge base with advanced features.
    Maintains simplicity while adding power features for multi-agent systems.
    """
    
    def __init__(self, storage_path: str = "enhanced_kb.json"):
        self.storage_path = Path(storage_path)
        self.entities: Dict[str, Entity] = {}
        self.relationships: Dict[str, Relationship] = {}
        self.embedder = EnhancedTFIDF()
        self.extractor = AdvancedEntityExtractor()
        
        # Enhanced metadata
        self.metadata = {
            'created_at': time.time(),
            'last_updated': time.time(),
            'version': '2.0',
            'total_entities': 0,
            'total_relationships': 0,
            'performance_stats': {},
            'schema_version': 1
        }
        
        # In-memory indexes for fast lookups
        self.entity_by_type: Dict[str, Set[str]] = defaultdict(set)
        self.entity_by_file: Dict[str, Set[str]] = defaultdict(set)
        self.relationship_by_type: Dict[str, Set[str]] = defaultdict(set)
    
    def ingest_file(self, file_path: str, content: str, incremental: bool = True):
        """Enhanced file ingestion with relationship extraction."""
        start_time = time.time()
        
        # Extract entities and relationships
        new_entities, new_relationships = self.extractor.extract_from_content(content, file_path)
        
        # Remove old entities from this file if doing incremental update
        if incremental:
            old_entities = list(self.entity_by_file[file_path])
            for entity_id in old_entities:
                self._remove_entity(entity_id)
        
        # Add new entities
        for entity in new_entities:
            self.entities[entity.id] = entity
            self.entity_by_type[entity.entity_type].add(entity.id)
            self.entity_by_file[entity.file_path].add(entity.id)
        
        # Add relationships
        for relationship in new_relationships:
            rel_id = f"{relationship.source_id}:{relationship.relationship_type}:{relationship.target_id}"
            self.relationships[rel_id] = relationship
            self.relationship_by_type[relationship.relationship_type].add(rel_id)
            
            # Add bidirectional references to entities
            if relationship.source_id in self.entities:
                if relationship.target_id not in self.entities[relationship.source_id].relationships:
                    self.entities[relationship.source_id].relationships.append(relationship.target_id)
        
        # Rebuild index (could be optimized for incremental)
        self._rebuild_index(incremental=incremental)
        
        ingest_time = time.time() - start_time
        self.metadata['performance_stats']['last_ingest_time'] = ingest_time
        
        return len(new_entities), len(new_relationships)
    
    def _remove_entity(self, entity_id: str):
        """Remove entity and clean up indexes."""
        if entity_id in self.entities:
            entity = self.entities[entity_id]
            
            # Remove from type index
            self.entity_by_type[entity.entity_type].discard(entity_id)
            
            # Remove from file index
            self.entity_by_file[entity.file_path].discard(entity_id)
            
            # Remove relationships
            rels_to_remove = [rel_id for rel_id, rel in self.relationships.items() 
                             if rel.source_id == entity_id or rel.target_id == entity_id]
            for rel_id in rels_to_remove:
                rel = self.relationships[rel_id]
                self.relationship_by_type[rel.relationship_type].discard(rel_id)
                del self.relationships[rel_id]
            
            # Remove entity
            del self.entities[entity_id]
    
    def _rebuild_index(self, incremental: bool = False):
        """Rebuild the enhanced index."""
        start_time = time.time()
        
        entity_list = list(self.entities.values())
        self.embedder.build_vocabulary(entity_list, incremental=incremental)
        
        self.metadata['last_updated'] = time.time()
        self.metadata['total_entities'] = len(self.entities)
        self.metadata['total_relationships'] = len(self.relationships)
        self.metadata['performance_stats']['index_build_time'] = time.time() - start_time
    
    def enhanced_search(self, 
                       query: str,
                       limit: int = 10,
                       min_relevance: float = 0.1,
                       entity_types: Optional[List[str]] = None,
                       include_relationships: bool = True,
                       boost_recent: bool = False) -> List[SearchResult]:
        """Enhanced search with filtering and relationship traversal."""
        start_time = time.time()
        
        if not self.entities:
            return []
        
        # Generate query vector
        query_vector = self.embedder.query_vector(query)
        if not query_vector:
            return []
        
        # Filter entities by type if specified
        candidate_entities = self.entities
        if entity_types:
            candidate_ids = set()
            for entity_type in entity_types:
                candidate_ids.update(self.entity_by_type.get(entity_type, set()))
            candidate_entities = {eid: e for eid, e in self.entities.items() if eid in candidate_ids}
        
        # Calculate similarities
        results = []
        query_terms = set(query_vector.keys())
        
        for entity_id, entity in candidate_entities.items():
            similarity = self.embedder.cosine_similarity(query_vector, entity_id)
            
            # Apply boosting
            if boost_recent:
                # Boost entities from recently modified files (placeholder logic)
                similarity *= 1.1
            
            if similarity >= min_relevance:
                # Find matching terms
                entity_terms = set(self.embedder.tf_idf_vectors.get(entity_id, {}).keys())
                matching_terms = list(query_terms & entity_terms)
                
                # Create explanation
                explanation = self._generate_explanation(entity, similarity, matching_terms)
                
                result = SearchResult(
                    entity=entity,
                    relevance_score=similarity,
                    matching_terms=matching_terms,
                    context={
                        'query_time': time.time() - start_time,
                        'has_relationships': len(entity.relationships) > 0
                    },
                    explanation=explanation
                )
                results.append(result)
        
        # Sort by relevance
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Optionally include related entities
        if include_relationships and results:
            results = self._expand_with_relationships(results, limit * 2)
        
        # Update performance stats
        query_time = time.time() - start_time
        self.metadata['performance_stats']['last_query_time'] = query_time
        
        return results[:limit]
    
    def _generate_explanation(self, entity: Entity, similarity: float, matching_terms: List[str]) -> str:
        """Generate human-readable explanation for search result."""
        explanation_parts = []
        
        if similarity > 0.7:
            explanation_parts.append("High relevance")
        elif similarity > 0.4:
            explanation_parts.append("Medium relevance")
        else:
            explanation_parts.append("Low relevance")
        
        if matching_terms:
            explanation_parts.append(f"matches: {', '.join(matching_terms[:3])}")
        
        if entity.relationships:
            explanation_parts.append(f"has {len(entity.relationships)} relationships")
        
        return " - ".join(explanation_parts)
    
    def _expand_with_relationships(self, results: List[SearchResult], max_results: int) -> List[SearchResult]:
        """Expand results with related entities."""
        expanded_results = results[:]
        seen_entities = {r.entity.id for r in results}
        
        for result in results:
            if len(expanded_results) >= max_results:
                break
            
            # Add related entities with lower scores
            for related_id in result.entity.relationships:
                if related_id in self.entities and related_id not in seen_entities:
                    related_entity = self.entities[related_id]
                    
                    # Create related result with reduced score
                    related_result = SearchResult(
                        entity=related_entity,
                        relevance_score=result.relevance_score * 0.7,  # Reduce score for related items
                        matching_terms=[],
                        context={'relationship': 'related'},
                        explanation=f"Related to {result.entity.metadata.get('name', 'matched entity')}"
                    )
                    
                    expanded_results.append(related_result)
                    seen_entities.add(related_id)
                    
                    if len(expanded_results) >= max_results:
                        break
        
        return expanded_results
    
    def get_relationships(self, entity_id: str, relationship_types: Optional[List[str]] = None) -> List[Relationship]:
        """Get relationships for an entity."""
        relationships = []
        
        for rel in self.relationships.values():
            if rel.source_id == entity_id or rel.target_id == entity_id:
                if not relationship_types or rel.relationship_type in relationship_types:
                    relationships.append(rel)
        
        return sorted(relationships, key=lambda x: x.strength, reverse=True)
    
    def suggest_similar_entities(self, entity_id: str, limit: int = 5) -> List[SearchResult]:
        """Find entities similar to a given entity."""
        if entity_id not in self.entities:
            return []
        
        entity = self.entities[entity_id]
        
        # Use entity content as query
        return self.enhanced_search(
            query=entity.content,
            limit=limit + 1,  # +1 because we'll filter out the original
            entity_types=[entity.entity_type]  # Same type
        )[1:]  # Remove the original entity
    
    def save_to_disk(self, compress: bool = True):
        """Save enhanced KB with optional compression."""
        data = {
            'metadata': self.metadata,
            'entities': {eid: asdict(entity) for eid, entity in self.entities.items()},
            'relationships': {rid: asdict(rel) for rid, rel in self.relationships.items()},
            'vocabulary': self.embedder.vocabulary,
            'document_frequency': self.embedder.document_frequency,
            'tf_idf_vectors': self.embedder.tf_idf_vectors
        }
        
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=None if compress else 2, default=str)
    
    def load_from_disk(self) -> bool:
        """Load enhanced KB from disk."""
        if not self.storage_path.exists():
            return False
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load basic data
            self.metadata = data['metadata']
            self.entities = {eid: Entity(**entity_data) for eid, entity_data in data['entities'].items()}
            self.relationships = {rid: Relationship(**rel_data) for rid, rel_data in data.get('relationships', {}).items()}
            
            # Load embedder data
            self.embedder.vocabulary = data['vocabulary']
            self.embedder.document_frequency = data['document_frequency']
            self.embedder.tf_idf_vectors = data['tf_idf_vectors']
            self.embedder.total_documents = len(self.entities)
            
            # Rebuild indexes
            self._rebuild_indexes()
            
            return True
        except Exception as e:
            print(f"Error loading enhanced knowledge base: {e}")
            return False
    
    def _rebuild_indexes(self):
        """Rebuild in-memory indexes after loading."""
        self.entity_by_type.clear()
        self.entity_by_file.clear()
        self.relationship_by_type.clear()
        
        for entity in self.entities.values():
            self.entity_by_type[entity.entity_type].add(entity.id)
            self.entity_by_file[entity.file_path].add(entity.id)
        
        for relationship in self.relationships.values():
            self.relationship_by_type[relationship.relationship_type].add(f"{relationship.source_id}:{relationship.relationship_type}:{relationship.target_id}")
    
    def stats(self) -> Dict[str, Any]:
        """Get comprehensive KB statistics."""
        entity_types = {et: len(entities) for et, entities in self.entity_by_type.items()}
        relationship_types = {rt: len(rels) for rt, rels in self.relationship_by_type.items()}
        file_counts = {file_path: len(entities) for file_path, entities in self.entity_by_file.items()}
        
        return {
            'version': self.metadata.get('version', '2.0'),
            'total_entities': len(self.entities),
            'total_relationships': len(self.relationships),
            'vocabulary_size': len(self.embedder.vocabulary),
            'entity_types': entity_types,
            'relationship_types': relationship_types,
            'files_indexed': len(file_counts),
            'performance': self.metadata.get('performance_stats', {}),
            'storage_size_mb': self.storage_path.stat().st_size / (1024 * 1024) if self.storage_path.exists() else 0,
            'cache_size': len(self.embedder.query_cache)
        }