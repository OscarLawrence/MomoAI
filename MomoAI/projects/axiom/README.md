# Axiom - Coherent AI Collaboration Platform

## Purpose

Axiom is the foundation for building truly coherent AI tools. It provides a clean Progressive Web App interface that democratizes software creation beyond developers, enabling anyone to collaborate with AI to build software solutions.

**Core Problem**: Cannot build coherent system with incoherent tools. Current AI assistants have system message pollution, conflicting instructions, messy tool abstractions, and no coherence validation.

**Axiom Solution**: Clean PWA with formal contracts, pure model interface, no SDK pollution.

## Architecture

### PWA + FastAPI Stack
- **Local FastAPI backend** with pure HTTP client to Claude Sonnet 4
- **Progressive Web App frontend** for universal device access
- **WebSocket integration** for real-time task progress
- **Future-proof design** works local + remote deployment

### Staged Collaboration Workflow
1. **Vision**: Free-form problem exploration
2. **Architecture**: Solution design & validation  
3. **Implementation**: Autonomous AI execution
4. **Review**: Human evaluation & refinement

### Essential Coherent Tools
- Pure model interface (no system message pollution)
- Formal contract system (`@contract_enforced`)
- Simple function call tools: `read_file()`, `edit_file()`, `bash_exec()`
- Real-time coherence monitoring
- Docless architecture with auto-generated searchable knowledge base

## Key Features

- **Universal Access**: PWA works on any device without installation
- **Democratized Creation**: Café owner builds website without terminal skills
- **Clean Tool System**: Natural function calls instead of complex JSON
- **Real-time Collaboration**: Live task progress and stage transitions
- **Coherence Validation**: Formal contracts ensure logical consistency

## Implementation Status

**Current**: Basic CLI with contract system, usability issues
**Next Phase**: Full PWA implementation following IMPLEMENTATION_PLAN.md
**Bootstrap Strategy**: Use Axiom to rebuild itself with higher coherence

This follows the principle: "Cannot build coherent system with incoherent tools, but need tools to build tools."