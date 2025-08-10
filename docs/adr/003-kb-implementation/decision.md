ADR: KnowledgeBase Design for Momo Multi-Agent System
Status
Accepted

Context
Momo requires a shared, multi-agent KnowledgeBase (KB) that supports:

Unified handling of vector, graph, and document data

Immutable, versioned data with rollback capabilities

Multi-tiered storage with tunable pruning

Agent-optimized querying with enrichment and context compression

Local-first, privacy-preserving storage with optional LAN mode

Integration with Git/DVC for version control and data syncing

Operation on diverse hardware, including low-resource devices

Decision Summary
Decision Reasoning
Data Model: Immutable + Diff-based Versioning Enables efficient rollback, audit trails, and avoids mutation conflicts in multi-agent settings.
Storage Tiers: Cold, Store, Runtime Balances performance and resource use; runtime layer holds active context for speed; cold stores archives.
Pruning: Multi-Level and Tunable Uses frequency and recency metrics to prune data; both global and per-agent pruning strategies supported.
Serialization: Protobuf internally, JSON optionally Protobuf provides compact, fast, schema-evolvable storage; JSON used only for debugging and external API convenience.
Query Enrichment: Built-in NLP tools & compression Supports natural language queries translated to graph queries and compresses context for efficiency.
Git/DVC Integration Leverages existing dev workflow tools for production data versioning and multi-agent collaboration.
Multi-Machine Support: Optional LAN mode Designed for future extension without impacting primary single-machine performance.
Conflict Resolution: Last-write-wins, no concurrent write conflicts Momo agents won’t update the same data simultaneously, simplifying consistency management.

Consequences
Complexity is managed by layering and immutability but requires robust diff handling.

Rollback and pruning provide powerful state control, improving reliability and performance.

Serialization choices optimize for performance and flexibility across agent ecosystems.

Git/DVC integration enables seamless sync and auditing but demands careful commit management by agents.

Open Questions
Pruning thresholds and strategies will evolve with usage analytics.

Sync commit policies should follow standard Git workflows with manual commit triggers from agents.
