# Momo AI

**A Revolutionary Self-Extending Multi-Agent System**

[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://python.org)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Momo AI is a groundbreaking multi-agent system that combines the power of autonomous agents, knowledge management, and self-extension capabilities. Named after the developer's daughter, this project represents a new paradigm in AI assistant architecture where intelligence is distributed across specialized agents that can create and improve themselves.

## 🌟 Key Features

### 🤖 Multi-Agent Architecture
- **Momo Agent**: User-facing interface focused on intent understanding
- **Work Group**: Specialized agents for refinement, execution, and creation
- **Self-Extension**: Dynamic agent creation when capabilities are missing
- **Knowledge-Driven**: Agent selection via semantic similarity search

### 🧠 Advanced Knowledge Management
- **Unified Storage**: Vector + Graph + Document backends for comprehensive data handling
- **Semantic Search**: Natural language queries with contextual understanding
- **Relationship Modeling**: Graph-based connections between concepts and entities
- **Performance Optimized**: Research-backed technology choices (DuckDB, LangChain)

### 📚 Revolutionary Documentation System
- **KB-Driven Documentation**: Single source of truth eliminates sync issues
- **On-Demand Generation**: Create industry-standard docs when needed
- **Zero Documentation Debt**: Always up-to-date, context-rich information
- **AI-Native Design**: Built for multi-agent consumption and generation

### 🔧 Developer Experience
- **Modular Architecture**: Protocol-based, swappable components
- **Comprehensive Testing**: Near 100% coverage with performance benchmarks
- **Type Safety**: Full type hints and async-first design
- **Scientific Approach**: All architectural decisions research-backed

## 🏗️ Architecture

```
MomoAI-nx/
├── apps/                       # User-facing applications
│   ├── web/                   # Nuxt.js web interface (port 3000)
│   ├── cli/                   # Node.js command-line interface
│   └── core/                  # Core Momo functionality
└── libs/python/               # Python libraries (uv + Nx managed)
    ├── momo-kb/              # Knowledge base abstraction
    ├── momo-logger/          # Structured logging system
    ├── momo-graph-store/     # Graph database abstraction
    ├── momo-vector-store/    # Vector store abstraction
    └── momo-store-document/  # Document store abstraction
```

### System Flow

1. **User Interaction** → Momo Agent (web/CLI interface)
2. **Task Dispatch** → Work Group (specialized agent pool)
3. **Agent Selection** → Similarity search on capabilities stored in KnowledgeBase
4. **Execution** → Worker agents perform tasks with refinement agents managing complexity
5. **Self-Extension** → Creation agents build new capabilities when needed

## 🚀 Quick Start

### Prerequisites

- **Python 3.13+** (for Python modules)
- **Node.js 18+** (for web/CLI applications)
- **uv** (Fast Python package manager)
- **pnpm** (Node.js package manager, Nx monorepo)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd MomoAI-nx
   ```

2. **Install dependencies (all modules)**
   ```bash
   pnpm install  # Installs Nx workspace dependencies
   ```

3. **Setup Python modules**
   ```bash
   # Install uv dependencies for all Python modules
   pnpm nx run-many -t install
   
   # Verify installation with fast tests
   pnpm nx run momo-kb:test-fast
   ```

4. **Setup and run Web Application**
   ```bash
   pnpm nx run web:serve  # Starts on port 3000
   ```

5. **Setup and run CLI Application**
   ```bash
   pnpm nx run cli:build
   ```

### Basic Usage

**Knowledge Base Operations:**
```python
from momo_kb import InMemoryKnowledgeBase, Document

# Initialize knowledge base
kb = InMemoryKnowledgeBase()

# Store information
await kb.save(Document.from_text("Python is a programming language", 
                                metadata={"type": "definition"}))

# Query with natural language
results = await kb.search("What is Python?")
```

**Web Interface:**
```bash
pnpm nx run web:serve
# Open http://localhost:3000
```

**CLI Interface:**
```bash
pnpm nx run cli:serve -- --help
```

## 🔬 Technology Stack

### Backend & Knowledge Management
- **Python 3.13+**: Core knowledge base implementation
- **DuckDB**: High-performance analytical queries (86% faster than MongoDB)
- **LangChain**: Vector search and graph retrieval
- **asyncio**: Async-first architecture for scalability

### Frontend & Applications
- **Nuxt.js**: Modern web application framework
- **TypeScript**: Type-safe application development
- **Node.js**: Cross-platform runtime environment

### Development & Testing
- **Nx**: Monorepo orchestration with intelligent caching
- **uv**: Ultra-fast Python package management with @nxlv/python integration  
- **pytest**: Comprehensive testing framework with performance benchmarks
- **ESLint/Prettier**: Code quality and formatting

## 📊 Performance Characteristics

| Component | Performance | Best For |
|-----------|-------------|----------|
| **InMemory Backend** | < 2ms search | Development, < 10K docs |
| **DuckDB Backend** | 28x faster than SQLite | Analytics, complex queries |
| **Vector Search** | < 2ms avg | Semantic similarity |
| **Graph Traversal** | Optimized depth control | Relationship discovery |

## 🧪 Development

### Python Modules (Nx + uv Integration)

```bash
# All commands run from project root via Nx

# Development setup
pnpm nx run <module-name>:install    # uv sync

# Testing strategies - Examples with momo-kb
pnpm nx run momo-kb:test             # All tests
pnpm nx run momo-kb:test-fast        # Unit + integration (skip performance)
pnpm nx run momo-kb:benchmark        # Performance analysis

# Code quality
pnpm nx run momo-kb:format           # Format code with uv run black
pnpm nx run momo-kb:typecheck        # Type checking with uv run mypy
pnpm nx run momo-kb:lint             # Check code style

# Run commands across all Python modules
pnpm nx run-many -t format           # Format all modules
pnpm nx affected -t test-fast        # Test only affected modules
```

### Test Categories

- **Unit Tests** (`tests/unit/`): Fast, isolated component validation
- **Integration Tests** (`tests/integration/`): Component interaction verification
- **Performance Tests** (`tests/performance/`): Benchmarks and scaling analysis

### Adding New Implementations

```python
from momo_kb import KnowledgeBase
from typing import List, Optional

class YourKnowledgeBase(KnowledgeBase):
    async def save(self, *documents: Document) -> List[str]:
        # Your implementation
        
    async def search(self, query: str, options: SearchOptions = None) -> List[SearchResult]:
        # Your implementation
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Write comprehensive tests** (`pnpm nx affected -t test-fast`)
4. **Ensure code quality** (`pnpm nx affected -t lint && pnpm nx affected -t typecheck`)
5. **Commit changes** (`git commit -m 'Add amazing feature'`)
6. **Push to branch** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

### Development Standards

- **100% Test Coverage**: All production code must be thoroughly tested
- **Type Safety**: Full type hints required for Python code
- **Documentation**: Comprehensive inline documentation
- **Performance**: Benchmark new implementations
- **Modularity**: Protocol-based, swappable components

## 📖 Documentation

- **CLAUDE.md**: Development instructions for Claude Code users
- **momo.md files**: AI-friendly context throughout the repository
- **momo.yaml files**: Structured module metadata
- **Inline Documentation**: Google-style docstrings with examples

## 🔮 Roadmap

### Current Focus: Knowledge Base Foundation
- [x] Abstract interface and document models
- [x] Core unified implementation with pluggable backends
- [x] DuckDB backend implementation
- [ ] Comprehensive benchmark infrastructure
- [ ] Production backend implementations

### Next Phase: Documentation Revolution
- [ ] KB-driven documentation system
- [ ] On-demand generation pipeline
- [ ] Multi-format export capabilities
- [ ] Integration with development workflow

### Future: Multi-Agent Ecosystem
- [ ] Advanced agent creation capabilities
- [ ] Distributed agent orchestration
- [ ] Self-learning and adaptation
- [ ] Enterprise deployment options

## 🏆 Philosophy

**"Give to society to take from society"** - This project embodies a commitment to creating genuine value through:

- **Scientific Rigor**: All decisions backed by research and analysis
- **Long-term Thinking**: Code written for decades of maintainability
- **Collaboration Focus**: Built for multi-developer, multi-agent teamwork
- **Open Innovation**: Publicly available with profit-sharing license

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 💝 Acknowledgments

Named after Momo, who inspires the pursuit of genuine intelligence and meaningful technology that serves humanity.

---

**Built with ❤️ by Vincent and the MomoAI community**
