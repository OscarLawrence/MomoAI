# backends

Graph storage backend implementations. InMemoryGraphBackend for development, extensible to production backends.

**Current:** InMemory backend with full graph operations, query support, traversal capabilities.

**Future:** Neo4j (production), MemGraph (analytics), following same protocol interface.

**Interface:** BaseGraphBackend protocol ensures consistent API across implementations.