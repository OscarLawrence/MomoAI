"""Document backend interface and abstract base class."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Protocol


class DocumentBackend(Protocol):
    """Protocol for document storage backends (formerly key-value)."""

    async def put(self, key: str, value: Dict[str, Any]) -> bool:
        """Store document data."""
        ...

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve document data by key."""
        ...

    async def delete(self, key: str) -> bool:
        """Delete document data."""
        ...

    async def scan(
        self, pattern: Optional[str] = None, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Scan for matching documents."""
        ...


class BaseDocumentBackend(ABC):
    """Abstract base class for document backends."""

    @abstractmethod
    async def put(self, key: str, value: Dict[str, Any]) -> bool:
        """Store document data."""
        pass

    @abstractmethod
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve document data by key."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete document data."""
        pass

    @abstractmethod
    async def scan(
        self, pattern: Optional[str] = None, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Scan for matching documents."""
        pass
