# 📚 MomoAI Documentation Hub

**Your complete guide to MomoAI's architecture, decisions, and development.**

---

## 🧭 Navigation Guide

### 🏗️ **Architecture & Decisions**

> Core technical decisions with research backing

| Document                                                                          | Purpose                        | Status         |
| --------------------------------------------------------------------------------- | ------------------------------ | -------------- |
| **[ADR-001: Nx Monorepo](adr/001-nx-monorepo/decision.md)**                       | Monorepo orchestration choice  | ✅ Implemented |
| **[ADR-002: Python Package Manager](adr/002-python-package-manager/decision.md)** | uv selection for Python deps   | ✅ Implemented |
| **[ADR-003: Knowledge Base](adr/003-kb-implementation/decision.md)**              | KB architecture specifications | ✅ Implemented |
| **[ADR-004: Nx Restructuring](adr/004-nx-restructuring/)**                        | Project organization           | ✅ Implemented |
| **[ADR-005: Documentation](adr/005-documentation-restructuring/)**                | Documentation strategy         | ✅ Implemented |
| **[ADR-006: Vector Database](adr/006-vector-database-implementation/decision.md)** | Vector DB architecture          | 🚧 Proposed   |

### 🔬 **Research Foundation**

> Scientific analysis backing our technical choices

| Research Area              | Key Documents                                               | Impact                   |
| -------------------------- | ----------------------------------------------------------- | ------------------------ |
| **Monorepo Architecture**  | [Architecture Research](../research/monorepo-architecture/) | Nx adoption              |
| **Knowledge Base Systems** | [KB Research](../research/knowledge-base/)                  | Multi-agent KB design    |
| **Python Tooling**         | [Python Tools Research](../research/python-tooling/)        | uv + performance focus   |
| **Performance**            | [Benchmarking Strategy](../research/performance/)           | Data-driven optimization |
| **Project Management**     | [Retrospectives](../research/project-management/)           | Process improvement      |

### 🔄 **Implementation History**

> Real-world execution records and lessons learned

| Implementation                                                                                         | Date       | Outcome    | Lessons                               |
| ------------------------------------------------------------------------------------------------------ | ---------- | ---------- | ------------------------------------- |
| **[Complete Nx Migration](docs/adr/001-nx-monorepo/migration-guide.md)**                               | 2025-08-09 | ✅ Success | Nx ecosystem power                    |
| **[Documentation Enhancement](docs/adr/005-documentation-restructuring/implementation-2025-08-10.md)** | 2025-08-10 | ✅ Success | Systematic documentation improvements |

### 📋 **Development Standards**

> Conventions and best practices

- **[Nx Conventions](adr/001-nx-monorepo/conventions.md)** - Project structure and naming
- **[Python Standards](../research/python-tooling/)** - Code quality and testing
- **[ADR Templates](adr/)** - Decision documentation format

---

## 🎯 **Quick Start Paths**

### 👨‍💻 **New Developer**

1. **[Project Overview](../README.md)** - Understand MomoAI's vision
2. **[Nx Conventions](adr/001-nx-monorepo/conventions.md)** - Learn our structure
3. **[Development Guide](../README.md#-development)** - Start contributing

### 🏗️ **Architect/Lead**

1. **[Research Foundation](../research/)** - Understand our analysis
2. **[ADR Index](#-architecture--decisions)** - Review key decisions
3. **[Migration History](#-implementation-history)** - Learn from execution

### 🤖 **AI Agent/Assistant**

1. **[CLAUDE.md](../CLAUDE.md)** - Agent-specific instructions
2. **[Module momo.md files](../code/libs/)** - Context-rich module info
3. **[KB Architecture](adr/003-kb-implementation/)** - Agent knowledge system

---

## 🔍 **Search & Discovery**

### By Topic

- **Multi-Agent Systems**: [KB Research](../research/knowledge-base/), [ADR-003](adr/003-kb-implementation/)
- **Performance**: [Benchmarking](../research/performance/), [Python Tools](../research/python-tooling/)
- **Monorepo**: [Architecture Research](../research/monorepo-architecture/), [ADR-001](adr/001-nx-monorepo/)
- **Documentation**: [ADR-005](adr/005-documentation-restructuring/), This hub

### By Document Type

- **Decisions**: All files in [`adr/`](adr/) directory
- **Research**: All files in [`../research/`](../research/) directory
- **Implementation**: All files in [`../migrations/`](../migrations/) directory
- **Standards**: `conventions.md` and `migration-guide.md` in ADR folders

---

## 🔗 **Cross-References**

### Research → Decision → Implementation Flow

```
Research Phase         Decision Phase              Implementation Phase
     ↓                      ↓                           ↓
📊 Technology Analysis → 📋 ADR Documentation → 🔄 Migration Execution
📈 Benchmarking       → ⚖️  Trade-off Analysis  → 📝 Lessons Learned
🔬 Scientific Study   → 🎯 Success Metrics     → ✅ Validation Results
```

### Key Relationships

- **[Monorepo Research](../research/monorepo-architecture/)** → **[ADR-001](adr/001-nx-monorepo/)** → **[Nx Migration](../migrations/)**
- **[Python Tools Research](../research/python-tooling/)** → **[ADR-002](adr/002-python-package-manager/)** → **[uv Implementation](adr/002-python-package-manager/migration-guide.md)**
- **[KB Research](../research/knowledge-base/)** → **[ADR-003](adr/003-kb-implementation/)** → **[KB Implementation](../code/libs/python/momo-kb/)**

---

## 🛠️ **Maintenance Guide**

### Adding New Documentation

1. **Research** → Create in `../research/[topic]/`
2. **Decision** → Use [ADR Template](adr/) format
3. **Implementation** → Document in `../migrations/`
4. **Update This Hub** → Add cross-references

### Documentation Standards

- **Research**: Scientific rigor, methodology, findings, recommendations
- **ADRs**: Context, options, decision, consequences, validation
- **Migrations**: Step-by-step execution, issues, solutions, metrics
- **Cross-Reference**: Always link related documents

---

## 💡 **Philosophy**

> **"Research-Driven Development"** - Every significant decision is backed by thorough analysis, documented transparently, and executed with measurable outcomes.

This documentation system embodies:

- **🔬 Scientific Rigor**: Research before decisions
- **📋 Decision Transparency**: Clear rationale documentation
- **🔄 Implementation Reality**: Honest execution records
- **🔗 Knowledge Connections**: Cross-referenced learning

---

**Questions? Start with the [Project README](../README.md) or dive into [Research](../research/) → [Decisions](adr/) → [Implementation](../migrations/)**
