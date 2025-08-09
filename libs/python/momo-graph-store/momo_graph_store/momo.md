# momo_graph_store

Core module exports: GraphStore main interface, factory functions, InMemoryGraphBackend, custom exceptions.

**Usage:** `from momo_graph_store import GraphStore` - Simple interface with memory backend defaults.

**Extension:** Factory pattern supports adding Neo4j, MemGraph backends. Protocol-based for clean abstractions.

**Integration:** Full LangChain GraphStore compatibility for ecosystem interoperability.