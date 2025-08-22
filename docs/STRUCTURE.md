# Repository Structure Guide

## Organization Principles

This repository follows a clean separation between active development and archived materials:

1. **Active Development**: `MomoAI/` contains all current work
2. **Safe Archive**: Historical materials isolated from main development
3. **Clear Boundaries**: No mixing of experimental and production code

## Directory Purposes

### MomoAI/
The main coherent AI proof of concept system. This is where all active development happens.

**Key Components:**
- `projects/axiom/` - Clean CLI code assistant (bootstrap component)
- `projects/coherence/` - Coherence validation engine
- `projects/core/` - Core system components (knowledge, protocols, validation)
- `projects/parsers/` - Code and documentation parsing tools
- `projects/tools/om/` - Operational management tools
- `projects/momo/` - Main system interface and cycles

### archive/
Historical and experimental materials preserved for reference.

**Subdirectories:**
- `disasters/` - Past failure documentation (isolated to prevent agent panic)
- `research/` - Early research and brainstorming documents
- `trading_experiments/` - Trading bot side projects and experiments

### docs/
Repository-level documentation and guides.

## Development Workflow

1. **Primary Work**: Focus on `MomoAI/` directory
2. **Reference**: Use archive materials for context and learning
3. **Documentation**: Update docs when structure changes

## Archive Policy

- Archive materials are preserved but not actively maintained
- No dependencies between MomoAI and archive components
- Archive serves as historical record and learning resource

## Clean Separation Benefits

- Agents can work on MomoAI without encountering "disaster" content
- Clear focus on current vs historical work
- Preserved learning materials without workspace pollution
- Independent development environments