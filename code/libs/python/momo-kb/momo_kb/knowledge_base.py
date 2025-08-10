"""
Unified KnowledgeBase with clean, intuitive API.

Provides high-level interface for multi-backend knowledge operations.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import io
import base64

from .kb_core import KnowledgeBaseCore
from .unified_models import Document, Relationship, SearchResult, KnowledgeBaseStats, DocumentType


class KnowledgeBase(KnowledgeBaseCore):
    """
    High-level unified API for multi-backend knowledge operations.
    
    Provides clean, intuitive interface for inserting, searching, and managing
    knowledge across multiple specialized backends.
    """
    
    def __init__(self, backends: List[str] = None):
        super().__init__(backends)
        
    async def insert(self, *docs) -> List[str]:
        """
        Insert documents and relationships into the knowledge base.
        
        Args:
            *docs: Variable number of documents/relationships to insert.
                   Can be Document objects, Relationship objects, or dicts.
                   
        Returns:
            List of unified IDs for the inserted items.
        """
        if not self._initialized:
            raise RuntimeError("KnowledgeBase not initialized. Use async context manager.")
            
        inserted_ids = []
        
        for doc in docs:
            # Convert to unified format if needed
            unified_item = self._normalize_input(doc)
            
            # Route to appropriate backends
            backend_ids = await self._route_insert(unified_item)
            
            # Update item with backend IDs
            if isinstance(unified_item, Document):
                for backend_name, backend_id in backend_ids.items():
                    unified_item = unified_item.with_backend_id(backend_name, backend_id)
            elif isinstance(unified_item, Relationship):
                for backend_name, backend_id in backend_ids.items():
                    unified_item = unified_item.with_backend_id(backend_name, backend_id)
                    
            # Record operation
            self._record_operation(
                "insert",
                item_type=type(unified_item).__name__,
                item_id=unified_item.id,
                backend_ids=backend_ids
            )
            
            inserted_ids.append(unified_item.id)
            
        return inserted_ids
        
    async def delete(self, *ids) -> Dict[str, bool]:
        """
        Delete documents or relationships by their unified IDs.
        
        Args:
            *ids: Variable number of unified IDs to delete.
            
        Returns:
            Dict mapping each ID to deletion success status.
        """
        if not self._initialized:
            raise RuntimeError("KnowledgeBase not initialized. Use async context manager.")
            
        results = {}
        
        for item_id in ids:
            # Try to delete as document first, then as relationship
            doc_results = await self._route_delete(item_id, "document")
            rel_results = await self._route_delete(item_id, "relationship")
            
            # Consider successful if deleted from any backend
            success = any(doc_results.values()) or any(rel_results.values())
            results[item_id] = success
            
            # Record operation
            self._record_operation(
                "delete",
                item_id=item_id,
                success=success,
                doc_results=doc_results,
                rel_results=rel_results
            )
            
        return results
        
    async def search(
        self, 
        query: str, 
        filters: Optional[Dict] = None, 
        top_k: int = 10,
        **kwargs
    ) -> SearchResult:
        """
        Search for documents and relationships using natural language query.
        
        Args:
            query: Natural language search query.
            filters: Optional filters to apply (e.g., {"type": "person"}).
            top_k: Maximum number of results to return.
            **kwargs: Additional search arguments for future expansion.
            
        Returns:
            SearchResult with documents, relationships, and metadata.
        """
        if not self._initialized:
            raise RuntimeError("KnowledgeBase not initialized. Use async context manager.")
            
        # Route search to backends and merge results
        result = await self._route_search(query, filters, top_k)
        
        # Record operation
        self._record_operation(
            "search",
            query=query,
            filters=filters,
            top_k=top_k,
            results_count=result.total_results,
            search_time_ms=result.search_time_ms,
            backends_used=result.backends_used
        )
        
        return result
        
    async def roll(self, steps: int) -> None:
        """
        Rollback the last N operations across all backends.
        
        Args:
            steps: Number of operations to rollback.
        """
        if not self._initialized:
            raise RuntimeError("KnowledgeBase not initialized. Use async context manager.")
            
        await self._coordinated_rollback(steps)
        
    async def prune(self, mode: str = "auto", threshold: Optional[float] = None) -> Dict[str, Any]:
        """
        Prune data across backends to optimize performance.
        
        Args:
            mode: Pruning mode ("auto", "aggressive", "conservative").
            threshold: Custom threshold for pruning decisions.
            
        Returns:
            Dict with pruning results from each backend.
        """
        if not self._initialized:
            raise RuntimeError("KnowledgeBase not initialized. Use async context manager.")
            
        # For now, implement basic pruning
        # This will be expanded based on backend capabilities
        results = {}
        
        for backend_name, backend in self.backends.items():
            try:
                # Most backends don't have prune method yet, so skip for now
                results[backend_name] = {"status": "not_implemented"}
            except Exception as e:
                results[backend_name] = {"status": "error", "error": str(e)}
                
        # Record operation
        self._record_operation(
            "prune",
            mode=mode,
            threshold=threshold,
            results=results
        )
        
        return results
        
    async def stats(self) -> KnowledgeBaseStats:
        """
        Get comprehensive statistics about the knowledge base state.
        
        Returns:
            KnowledgeBaseStats with counts, backend info, and system metrics.
        """
        if not self._initialized:
            raise RuntimeError("KnowledgeBase not initialized. Use async context manager.")
            
        # Collect stats from all backends
        backend_stats = {}
        total_docs = 0
        total_rels = 0
        doc_types = {}
        
        for backend_name, backend in self.backends.items():
            try:
                stats = await backend.get_stats()
                backend_stats[backend_name] = stats
                
                # Aggregate counts (rough estimates)
                if "nodes" in stats:
                    total_docs += stats["nodes"]
                if "edges" in stats:
                    total_rels += stats["edges"]
                    
            except Exception as e:
                backend_stats[backend_name] = {"error": str(e)}
                
        return KnowledgeBaseStats(
            total_documents=total_docs,
            total_relationships=total_rels,
            document_types=doc_types,  # Will be populated as we track document types
            active_backends=list(self.backends.keys()),
            backend_stats=backend_stats,
            created_at=self._created_at,
            total_operations=len(self._operation_history)
        )
        
    async def screenshot(self) -> str:
        """
        Generate a simple matplotlib visualization of the knowledge base.
        
        Returns:
            Base64-encoded PNG image of the knowledge base visualization.
        """
        if not self._initialized:
            raise RuntimeError("KnowledgeBase not initialized. Use async context manager.")
            
        # Get current stats
        stats = await self.stats()
        
        # Create figure
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Momo KnowledgeBase Overview', fontsize=16, fontweight='bold')
        
        # 1. Backend Status
        backend_names = list(stats.active_backends)
        backend_counts = [stats.backend_stats.get(name, {}).get('nodes', 0) for name in backend_names]
        
        ax1.bar(backend_names, backend_counts, color=['#2E8B57', '#FF6B6B', '#4ECDC4', '#45B7D1'])
        ax1.set_title('Documents by Backend')
        ax1.set_ylabel('Document Count')
        
        # 2. Document Types (pie chart)
        if stats.document_types:
            ax2.pie(stats.document_types.values(), labels=stats.document_types.keys(), autopct='%1.1f%%')
            ax2.set_title('Document Types Distribution')
        else:
            ax2.text(0.5, 0.5, 'No document\ntype data', ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Document Types Distribution')
            
        # 3. Operations Timeline (simple bar)
        recent_ops = self._operation_history[-10:] if len(self._operation_history) > 10 else self._operation_history
        op_types = [op.get('type', 'unknown') for op in recent_ops]
        op_counts = {}
        for op_type in op_types:
            op_counts[op_type] = op_counts.get(op_type, 0) + 1
            
        if op_counts:
            ax3.bar(op_counts.keys(), op_counts.values(), color='#9B59B6')
            ax3.set_title('Recent Operations (Last 10)')
            ax3.set_ylabel('Count')
        else:
            ax3.text(0.5, 0.5, 'No operations\nyet', ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Recent Operations')
            
        # 4. System Info
        info_text = f"""
        Total Documents: {stats.total_documents:,}
        Total Relationships: {stats.total_relationships:,}
        Active Backends: {len(stats.active_backends)}
        Total Operations: {stats.total_operations:,}
        
        Created: {stats.created_at.strftime('%Y-%m-%d %H:%M')}
        Last Updated: {stats.last_updated.strftime('%Y-%m-%d %H:%M')}
        """
        
        ax4.text(0.1, 0.9, info_text.strip(), transform=ax4.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace')
        ax4.set_title('System Information')
        ax4.axis('off')
        
        # Adjust layout
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
        
    def _normalize_input(self, item: Any) -> Union[Document, Relationship]:
        """Convert various input formats to unified Document or Relationship."""
        if isinstance(item, (Document, Relationship)):
            return item
            
        if isinstance(item, dict):
            # Detect if it's a relationship or document
            if "source_id" in item and "target_id" in item and "relationship_type" in item:
                # It's a relationship
                return Relationship(**item)
            else:
                # It's a document
                # Handle various dict formats
                doc_data = item.copy()
                
                # Ensure required fields
                if "type" not in doc_data:
                    doc_data["type"] = DocumentType.CUSTOM
                elif isinstance(doc_data["type"], str):
                    doc_data["type"] = DocumentType(doc_data["type"])
                    
                return Document(**doc_data)
                
        elif isinstance(item, str):
            # Raw text content
            return Document(
                type=DocumentType.DOCUMENT,
                content=item,
                title=item[:50] + "..." if len(item) > 50 else item
            )
            
        else:
            raise ValueError(f"Unsupported input type: {type(item)}")
            
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False