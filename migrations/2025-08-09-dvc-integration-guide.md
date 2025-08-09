# DVC Integration Migration Guide

**Date**: 2025-08-09  
**Status**: Implementation Ready  
**Scope**: MomoAI mono-repo DVC integration for MLOps workflow

## Overview

This migration integrates Data Version Control (DVC) into the MomoAI mono-repo to enable:
- **Development**: Team collaboration on knowledge base artifacts
- **Deployment**: Local-only knowledge encapsulation with user privacy
- **MLOps**: Reproducible ML pipelines with scientific rigor

## Architecture Strategy

### Two-Tier DVC Approach

#### Development Phase (Team Collaboration)
- **Purpose**: Share processed knowledge base artifacts during development
- **Storage**: Local remote on Bullenwinkel infrastructure
- **Scope**: Core system knowledge, processing pipelines, benchmarks

#### Deployment Phase (User Privacy)
- **Purpose**: Complete local encapsulation of user data
- **Storage**: Local-only with no remote dependencies
- **Scope**: User-specific knowledge, private documents, local cache

## Migration Steps

### Phase 1: Core DVC Setup

#### 1.1 Install DVC Dependencies
```bash
# Add DVC to Python modules that need it
cd libs/python/momo-kb
uv add dvc duckdb

cd ../momo-vector-store
uv add dvc

cd ../momo-graph-store  
uv add dvc

cd ../momo-store-document
uv add dvc
```

#### 1.2 Initialize DVC at Repository Root
```bash
cd /home/vincent/Documents/Momo/MomoAI-nx
dvc init --no-scm
git add .dvc/
git commit -m "Initialize DVC for MLOps workflow"
```

#### 1.3 Configure Local Development Remote
```bash
# Configure local NAS/server storage
dvc remote add -d dev-remote ssh://vincent@bullenwinkel-server/momo-dev-kb
# Or local filesystem
dvc remote add -d dev-remote /path/to/nas/momo-dev-kb

git add .dvc/config
git commit -m "Configure development DVC remote"
```

### Phase 2: Directory Structure Setup

#### 2.1 Create Data Directories
```bash
# Root-level shared data
mkdir -p data/{raw,processed,models,knowledge-base}

# Module-specific data directories
mkdir -p libs/python/momo-kb/data/{embeddings,indices}
mkdir -p libs/python/momo-vector-store/data/{vectors,benchmarks}
mkdir -p libs/python/momo-graph-store/data/{graphs,schemas}
mkdir -p libs/python/momo-store-document/data/{documents,metadata}

# App-specific data
mkdir -p apps/core/data/{agents,pipelines}
```

#### 2.2 Create .gitignore Entries
```bash
# Add to .gitignore
echo "# DVC managed data" >> .gitignore
echo "/data/" >> .gitignore
echo "*/data/" >> .gitignore
echo "*.dvc" >> .gitignore

git add .gitignore
git commit -m "Add DVC data directories to gitignore"
```

### Phase 3: Pipeline Definition

#### 3.1 Root-level DVC Pipeline
Create `dvc.yaml`:
```yaml
stages:
  kb-ingest:
    cmd: python scripts/kb-ingest.py
    deps:
      - libs/python/*/momo_*/
      - libs/python/*/momo.md
      - apps/*/
    outs:
      - data/knowledge-base/
      - data/vectors/
      - data/graphs/
    params:
      - kb_config.embedding_model
      - kb_config.chunk_size
    
  docs-generate:
    cmd: python scripts/docs-generate.py
    deps:
      - data/knowledge-base/
    outs:
      - docs/generated/
    
  benchmark-kb:
    cmd: python scripts/benchmark-kb.py
    deps:
      - data/knowledge-base/
    metrics:
      - benchmarks/kb_metrics.json
```

#### 3.2 Module-specific Pipelines
For each Python module, create module-specific `dvc.yaml`:

**libs/python/momo-kb/dvc.yaml**:
```yaml
stages:
  process-embeddings:
    cmd: uv run python scripts/process_embeddings.py
    deps:
      - momo_kb/
      - ../../../data/raw/
    outs:
      - data/embeddings/
      - data/indices/
    metrics:
      - benchmarks/embedding_metrics.json
```

### Phase 4: Nx Integration

#### 4.1 Update nx.json Target Defaults
```json
{
  "targetDefaults": {
    "dvc-repro": {
      "cache": false,
      "dependsOn": ["format", "typecheck"]
    },
    "dvc-pull": {
      "cache": false
    },
    "dvc-push": {
      "cache": false
    },
    "dvc-ingest": {
      "cache": false,
      "dependsOn": ["test-all"]
    }
  }
}
```

#### 4.2 Add DVC Commands to Python Modules
Update each module's `project.json`:
```json
{
  "targets": {
    "dvc-repro": {
      "executor": "nx:run-commands",
      "options": {
        "cwd": "{projectRoot}",
        "commands": ["dvc repro"]
      }
    },
    "dvc-pull": {
      "executor": "nx:run-commands", 
      "options": {
        "cwd": "{projectRoot}",
        "commands": ["dvc pull"]
      }
    },
    "kb-ingest": {
      "executor": "nx:run-commands",
      "options": {
        "commands": [
          "dvc repro kb-ingest",
          "dvc push"
        ]
      },
      "dependsOn": ["test-all"]
    }
  }
}
```

### Phase 5: Knowledge Base Integration Scripts

#### 5.1 Create KB Ingestion Script
Create `scripts/kb-ingest.py`:
```python
#!/usr/bin/env python3
"""
Knowledge Base Ingestion Pipeline
Processes source code into knowledge artifacts
"""
import asyncio
from pathlib import Path
from momo_kb import KnowledgeBase
from momo_vector_store import VectorStore
from momo_graph_store import GraphStore

async def ingest_codebase():
    """Ingest entire codebase into knowledge base"""
    kb = KnowledgeBase()
    
    # Process all Python modules
    for module_path in Path("libs/python").glob("momo-*"):
        if module_path.is_dir():
            await kb.ingest_module(module_path)
    
    # Process apps
    for app_path in Path("apps").glob("*"):
        if app_path.is_dir():
            await kb.ingest_app(app_path)
    
    # Generate knowledge artifacts
    await kb.build_vectors("data/vectors/")
    await kb.build_graphs("data/graphs/") 
    await kb.export_knowledge("data/knowledge-base/")

if __name__ == "__main__":
    asyncio.run(ingest_codebase())
```

#### 5.2 Create Documentation Generation Script  
Create `scripts/docs-generate.py`:
```python
#!/usr/bin/env python3
"""
On-demand Documentation Generation
Generates contextual docs from knowledge base
"""
import asyncio
from pathlib import Path
from momo_kb import KnowledgeBase

async def generate_docs():
    """Generate documentation from knowledge base"""
    kb = KnowledgeBase.load("data/knowledge-base/")
    
    # Generate module docs
    for module in kb.get_modules():
        doc = await kb.generate_docs(
            module=module,
            style="developer",
            format="markdown"
        )
        
        output_path = Path(f"docs/generated/{module.name}.md")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(doc)

if __name__ == "__main__":
    asyncio.run(generate_docs())
```

### Phase 6: Development Workflow Integration

#### 6.1 Update CLAUDE.md Commands
Add to root CLAUDE.md:
```markdown
### DVC MLOps Commands

# Core workflow
nx run-many -t dvc-pull          # Pull latest KB artifacts
nx run kb-ingest                 # Process code into KB artifacts  
nx run docs-generate             # Generate fresh documentation
nx run-many -t dvc-push         # Share KB artifacts with team

# Module-specific
nx run momo-kb:dvc-repro        # Rebuild KB module artifacts
nx run momo-vector-store:dvc-repro  # Rebuild vector artifacts
```

#### 6.2 Pre-commit Hook Integration
Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: dvc-check
        name: DVC Pipeline Check
        entry: dvc status
        language: system
        pass_filenames: false
```

### Phase 7: Deployment Preparation

#### 7.1 Create Deployment DVC Config
Create `deployment/.dvc/config`:
```ini
[core]
    remote = 
    cache = ~/.momo/cache
    
['remote "local-cache"']
    url = ~/.momo/data
```

#### 7.2 Freeze Core Knowledge Base
```python
# scripts/freeze-kb.py
"""Freeze core KB for deployment"""
import dvc.api

def freeze_core_kb():
    """Create immutable core knowledge base"""
    # Freeze current KB state
    dvc.api.get_url("data/knowledge-base/", rev="v1.0.0")
    
    # Package for deployment
    # This becomes part of the installer
```

## Usage Workflows

### Development Workflow
1. **Start work**: `nx run-many -t dvc-pull`
2. **Code changes**: Normal development
3. **Update KB**: `nx run kb-ingest` 
4. **Generate docs**: `nx run docs-generate`
5. **Share changes**: `nx run-many -t dvc-push`

### Testing Workflow
1. **Ensure KB current**: `dvc status`
2. **Run tests**: `nx run-many -t test-all`
3. **Benchmark**: `nx run-many -t benchmark`

### Release Workflow
1. **Full KB rebuild**: `dvc repro`
2. **Generate release docs**: `nx run docs-generate`
3. **Freeze KB state**: `dvc freeze`
4. **Package for deployment**: Include frozen KB in installer

## Privacy & Security Considerations

### Development Phase
- KB artifacts shared within team
- No user data in development KB
- All artifacts versioned and reproducible

### Deployment Phase
- Core KB ships with application (frozen)
- User KB remains local and encrypted
- No remote dependencies post-installation
- Optional user-controlled remote backup

## File Structure After Migration

```
MomoAI-nx/
├── .dvc/                    # DVC configuration
├── dvc.yaml                 # Root pipeline definition
├── data/                    # DVC-managed artifacts
│   ├── knowledge-base/      # Processed KB artifacts
│   ├── vectors/             # Vector embeddings  
│   ├── graphs/              # Knowledge graphs
│   └── models/              # Trained models
├── scripts/                 # DVC pipeline scripts
│   ├── kb-ingest.py         # KB ingestion pipeline
│   ├── docs-generate.py     # Documentation generation
│   └── freeze-kb.py         # Deployment preparation
├── libs/python/
│   └── momo-*/
│       ├── dvc.yaml         # Module-specific pipelines
│       └── data/            # Module-specific artifacts
└── deployment/
    └── .dvc/                # Deployment DVC config
```

## Success Criteria

- [ ] DVC initialized and configured
- [ ] All modules can run `dvc repro` successfully  
- [ ] Knowledge base artifacts version correctly
- [ ] Documentation generates from KB
- [ ] Nx commands integrate DVC workflow
- [ ] No external dependencies in deployment mode
- [ ] User privacy maintained in deployed instances

## Rollback Plan

If issues arise:
1. `git checkout HEAD~1 .dvc/` - Revert DVC config
2. `rm -rf data/` - Remove DVC-managed directories
3. `git reset --hard` - Return to pre-migration state

## Next Steps

After migration:
1. Implement `momo-docs` module with living documentation
2. Add ML experiment tracking with DVC experiments
3. Integrate with CI/CD for automated KB updates
4. Add performance monitoring for KB operations