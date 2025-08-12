"""
DVC Manager - Integration with DVC for immutable knowledge base versioning.

Handles snapshot persistence, version tracking, and reproducible knowledge management.
"""

import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import time

from .models import KnowledgeBaseSnapshot


class DVCManager:
    """
    Manages DVC integration for knowledge base versioning.
    
    Provides:
    1. Snapshot persistence with DVC tracking
    2. Version history management
    3. Reproducible knowledge base states
    4. Efficient storage with deduplication
    """
    
    def __init__(self, data_dir: Path):
        """
        Initialize DVC manager.
        
        Args:
            data_dir: Base directory for data storage
        """
        self.data_dir = Path(data_dir)
        self.snapshots_dir = self.data_dir / "snapshots"
        self.operations_dir = self.data_dir / "operations"
        self.metadata_dir = self.data_dir / "metadata"
        
        # Create directories
        for dir_path in [self.snapshots_dir, self.operations_dir, self.metadata_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # Initialize DVC if not already done
        self._ensure_dvc_initialized()
        
    def _ensure_dvc_initialized(self) -> None:
        """Ensure DVC is initialized in the data directory."""
        dvc_dir = self.data_dir / ".dvc"
        if not dvc_dir.exists():
            try:
                # Initialize DVC
                subprocess.run(
                    ["dvc", "init", "--no-scm"],
                    cwd=self.data_dir,
                    check=True,
                    capture_output=True
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                # DVC not available or failed - continue without it
                pass
                
    def save_snapshot(self, snapshot: KnowledgeBaseSnapshot) -> bool:
        """
        Save snapshot with DVC tracking.
        
        Args:
            snapshot: Snapshot to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Create snapshot file
            snapshot_file = self.snapshots_dir / f"snapshot_v{snapshot.version:06d}.json"
            
            # Save snapshot metadata
            snapshot_data = {
                "snapshot": snapshot.model_dump(),
                "saved_at": time.time(),
                "format_version": "1.0"
            }
            
            with open(snapshot_file, 'w') as f:
                json.dump(snapshot_data, f, indent=2, default=str)
                
            # Save lattice data separately for efficiency
            lattice_data = snapshot.metadata.get("lattice_snapshot")
            if lattice_data:
                lattice_file = self.snapshots_dir / f"lattice_v{snapshot.version:06d}.pkl"
                with open(lattice_file, 'wb') as f:
                    pickle.dump(lattice_data, f)
                    
            # Add to DVC tracking
            self._add_to_dvc(snapshot_file)
            self._add_to_dvc(lattice_file)
            
            # Update metadata index
            self._update_metadata_index(snapshot)
            
            return True
            
        except Exception as e:
            print(f"Failed to save snapshot: {e}")
            return False
            
    def load_snapshot(self, version: int) -> Optional[KnowledgeBaseSnapshot]:
        """
        Load snapshot by version.
        
        Args:
            version: Snapshot version to load
            
        Returns:
            Loaded snapshot or None if not found
        """
        try:
            snapshot_file = self.snapshots_dir / f"snapshot_v{version:06d}.json"
            lattice_file = self.snapshots_dir / f"lattice_v{version:06d}.pkl"
            
            if not snapshot_file.exists():
                return None
                
            # Load snapshot metadata
            with open(snapshot_file, 'r') as f:
                snapshot_data = json.load(f)
                
            snapshot_dict = snapshot_data["snapshot"]
            
            # Load lattice data if available
            if lattice_file.exists():
                with open(lattice_file, 'rb') as f:
                    lattice_data = pickle.load(f)
                    snapshot_dict["metadata"]["lattice_snapshot"] = lattice_data
                    
            return KnowledgeBaseSnapshot(**snapshot_dict)
            
        except Exception as e:
            print(f"Failed to load snapshot v{version}: {e}")
            return None
            
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """
        List all available snapshots.
        
        Returns:
            List of snapshot metadata
        """
        snapshots = []
        
        for snapshot_file in sorted(self.snapshots_dir.glob("snapshot_v*.json")):
            try:
                with open(snapshot_file, 'r') as f:
                    data = json.load(f)
                    
                snapshot_info = {
                    "version": data["snapshot"]["version"],
                    "timestamp": data["snapshot"]["timestamp"],
                    "operation_count": data["snapshot"]["operation_count"],
                    "document_count": data["snapshot"]["document_count"],
                    "relationship_count": data["snapshot"]["relationship_count"],
                    "file_path": str(snapshot_file),
                    "saved_at": data.get("saved_at"),
                }
                snapshots.append(snapshot_info)
                
            except Exception as e:
                print(f"Failed to read snapshot {snapshot_file}: {e}")
                continue
                
        return snapshots
        
    def cleanup_old_snapshots(self, keep_versions: int = 10) -> int:
        """
        Clean up old snapshots, keeping only the most recent versions.
        
        Args:
            keep_versions: Number of recent versions to keep
            
        Returns:
            Number of snapshots removed
        """
        snapshots = self.list_snapshots()
        
        if len(snapshots) <= keep_versions:
            return 0
            
        # Sort by version and remove oldest
        snapshots.sort(key=lambda x: x["version"], reverse=True)
        to_remove = snapshots[keep_versions:]
        
        removed_count = 0
        for snapshot_info in to_remove:
            try:
                version = snapshot_info["version"]
                
                # Remove files
                snapshot_file = self.snapshots_dir / f"snapshot_v{version:06d}.json"
                lattice_file = self.snapshots_dir / f"lattice_v{version:06d}.pkl"
                
                if snapshot_file.exists():
                    snapshot_file.unlink()
                if lattice_file.exists():
                    lattice_file.unlink()
                    
                removed_count += 1
                
            except Exception as e:
                print(f"Failed to remove snapshot v{version}: {e}")
                continue
                
        return removed_count
        
    def _add_to_dvc(self, file_path: Path) -> None:
        """Add file to DVC tracking."""
        try:
            subprocess.run(
                ["dvc", "add", str(file_path)],
                cwd=self.data_dir,
                check=True,
                capture_output=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # DVC not available or failed - continue without it
            pass
            
    def _update_metadata_index(self, snapshot: KnowledgeBaseSnapshot) -> None:
        """Update metadata index for fast queries."""
        index_file = self.metadata_dir / "snapshot_index.json"
        
        # Load existing index
        index = {}
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    index = json.load(f)
            except Exception:
                index = {}
                
        # Add new snapshot to index
        index[str(snapshot.version)] = {
            "id": snapshot.id,
            "version": snapshot.version,
            "timestamp": snapshot.timestamp.isoformat(),
            "operation_count": snapshot.operation_count,
            "document_count": snapshot.document_count,
            "relationship_count": snapshot.relationship_count,
            "checksum": snapshot.checksum,
        }
        
        # Save updated index
        try:
            with open(index_file, 'w') as f:
                json.dump(index, f, indent=2)
        except Exception as e:
            print(f"Failed to update metadata index: {e}")
            
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        stats = {
            "snapshots_dir": str(self.snapshots_dir),
            "total_snapshots": len(list(self.snapshots_dir.glob("snapshot_v*.json"))),
            "total_lattice_files": len(list(self.snapshots_dir.glob("lattice_v*.pkl"))),
        }
        
        # Calculate total size
        total_size = 0
        for file_path in self.snapshots_dir.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size
                
        stats["total_size_bytes"] = total_size
        stats["total_size_mb"] = total_size / (1024 * 1024)
        
        return stats
        
    def export_snapshot(self, version: int, export_path: Path) -> bool:
        """
        Export snapshot to external location.
        
        Args:
            version: Snapshot version to export
            export_path: Destination path
            
        Returns:
            True if exported successfully
        """
        try:
            snapshot = self.load_snapshot(version)
            if not snapshot:
                return False
                
            export_path.mkdir(parents=True, exist_ok=True)
            
            # Export snapshot data
            export_file = export_path / f"kb_snapshot_v{version}.json"
            with open(export_file, 'w') as f:
                json.dump(snapshot.model_dump(), f, indent=2, default=str)
                
            return True
            
        except Exception as e:
            print(f"Failed to export snapshot v{version}: {e}")
            return False
            
    def import_snapshot(self, import_path: Path) -> Optional[KnowledgeBaseSnapshot]:
        """
        Import snapshot from external location.
        
        Args:
            import_path: Path to snapshot file
            
        Returns:
            Imported snapshot or None if failed
        """
        try:
            with open(import_path, 'r') as f:
                snapshot_data = json.load(f)
                
            snapshot = KnowledgeBaseSnapshot(**snapshot_data)
            
            # Save imported snapshot
            if self.save_snapshot(snapshot):
                return snapshot
            else:
                return None
                
        except Exception as e:
            print(f"Failed to import snapshot from {import_path}: {e}")
            return None