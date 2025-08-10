# Momo KnowledgeBase Deployment Guide

## Production Deployment

### System Requirements

**Minimum Requirements:**
- Python 3.12+
- 4GB RAM
- 2 CPU cores
- 10GB storage

**Recommended for Production:**
- Python 3.12+
- 16GB+ RAM
- 8+ CPU cores
- 100GB+ SSD storage
- Load balancer for high availability

### Installation

```bash
# Clone repository
git clone <repository-url>
cd momo-kb

# Install with uv (recommended)
uv install --production

# Or with pip
pip install -e .
```

### Configuration

```python
# config.py
from momo_kb import KnowledgeBase

class ProductionConfig:
    # Storage tier limits
    RUNTIME_LIMIT = 10000  # nodes in memory
    STORE_LIMIT = 100000   # nodes in indexed storage
    
    # Performance settings
    QUERY_TIMEOUT = 30.0   # seconds
    BATCH_SIZE = 1000      # for bulk operations
    
    # Monitoring
    ENABLE_METRICS = True
    LOG_LEVEL = "INFO"

# Initialize with config
async def create_kb():
    kb = KnowledgeBase()
    await kb.initialize()
    return kb
```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install uv && uv install --production

EXPOSE 8000
CMD ["python", "-m", "momo_kb.server"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  momo-kb:
    build: .
    ports:
      - "8000:8000"
    environment:
      - RUNTIME_LIMIT=10000
      - STORE_LIMIT=100000
    volumes:
      - kb_data:/app/data
    restart: unless-stopped

volumes:
  kb_data:
```

### Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: momo-kb
spec:
  replicas: 3
  selector:
    matchLabels:
      app: momo-kb
  template:
    metadata:
      labels:
        app: momo-kb
    spec:
      containers:
      - name: momo-kb
        image: momo-kb:latest
        ports:
        - containerPort: 8000
        env:
        - name: RUNTIME_LIMIT
          value: "10000"
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "16Gi"
            cpu: "8"
---
apiVersion: v1
kind: Service
metadata:
  name: momo-kb-service
spec:
  selector:
    app: momo-kb
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Monitoring and Observability

### Health Checks

```python
# health.py
async def health_check(kb: KnowledgeBase):
    """Comprehensive health check."""
    try:
        # Basic connectivity
        node_count = await kb.count_nodes()
        
        # Performance check
        start = time.time()
        await kb.query_nodes(label="HealthCheck")
        query_time = time.time() - start
        
        # Memory usage
        runtime_count = await kb.count_nodes(tier="runtime")
        
        return {
            "status": "healthy",
            "node_count": node_count,
            "query_time_ms": query_time * 1000,
            "runtime_nodes": runtime_count,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
```

### Metrics Collection

```python
# metrics.py
import time
from typing import Dict, Any

class MetricsCollector:
    def __init__(self):
        self.metrics = {}
    
    async def collect_performance_metrics(self, kb: KnowledgeBase):
        """Collect key performance metrics."""
        metrics = {}
        
        # Storage metrics
        metrics["nodes_total"] = await kb.count_nodes()
        metrics["nodes_runtime"] = await kb.count_nodes(tier="runtime")
        metrics["nodes_store"] = await kb.count_nodes(tier="store")
        metrics["nodes_cold"] = await kb.count_nodes(tier="cold")
        
        metrics["edges_total"] = await kb.count_edges()
        
        # Performance metrics
        start = time.time()
        await kb.query_nodes(label="TestQuery")
        metrics["query_latency_ms"] = (time.time() - start) * 1000
        
        # History metrics
        history = await kb.get_diff_history()
        metrics["total_operations"] = len(history)
        
        return metrics
```

## Performance Tuning

### Memory Optimization

```python
# Tune storage tier limits based on available memory
async def optimize_memory_usage(kb: KnowledgeBase):
    """Optimize memory usage based on system resources."""
    import psutil
    
    # Get available memory
    memory = psutil.virtual_memory()
    available_gb = memory.available / (1024**3)
    
    # Calculate optimal limits
    runtime_limit = int(available_gb * 1000)  # ~1KB per node
    store_limit = runtime_limit * 10
    
    # Apply pruning
    await kb.prune(
        runtime_limit=runtime_limit,
        store_limit=store_limit
    )
```

### Query Optimization

```python
# Best practices for query performance
async def optimized_queries(kb: KnowledgeBase):
    """Examples of optimized query patterns."""
    
    # Efficient: Use indexed properties
    result = await kb.query_nodes(properties={"status": "active"})
    
    # Efficient: Combine label and properties
    result = await kb.query_nodes(
        label="Person",
        properties={"department": "Engineering"}
    )
    
    # Less efficient but still works: Complex properties
    # (Use sparingly)
    result = await kb.query_nodes(
        properties={"metadata": {"priority": "high"}}
    )
```

## Security Considerations

### Access Control

```python
# Simple access control example
class SecureKnowledgeBase:
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb
        self.permissions = {}
    
    async def query_nodes_with_auth(self, user_id: str, **kwargs):
        """Query nodes with user authentication."""
        if not self._has_read_permission(user_id):
            raise PermissionError("Insufficient permissions")
        
        return await self.kb.query_nodes(**kwargs)
    
    def _has_read_permission(self, user_id: str) -> bool:
        return self.permissions.get(user_id, {}).get("read", False)
```

### Data Encryption

```python
# Encrypt sensitive properties
import json
from cryptography.fernet import Fernet

class EncryptedProperties:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt_node(self, node: Node, sensitive_fields: list) -> Node:
        """Encrypt sensitive fields in node properties."""
        encrypted_props = node.properties.copy()
        
        for field in sensitive_fields:
            if field in encrypted_props:
                value = json.dumps(encrypted_props[field])
                encrypted_props[field] = self.cipher.encrypt(
                    value.encode()
                ).decode()
        
        return node.model_copy(update={"properties": encrypted_props})
```

## Backup and Recovery

### Data Export

```python
# Regular backup routine
async def backup_knowledge_base(kb: KnowledgeBase, backup_path: str):
    """Create complete backup of knowledge base."""
    import json
    from datetime import datetime
    
    # Export all data
    data = await kb.export_json()
    
    # Add backup metadata
    backup_data = {
        "backup_timestamp": datetime.utcnow().isoformat(),
        "version": "1.0",
        "data": data
    }
    
    # Write to file
    with open(backup_path, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    print(f"Backup completed: {backup_path}")
```

### Data Restoration

```python
# Restore from backup
async def restore_knowledge_base(kb: KnowledgeBase, backup_path: str):
    """Restore knowledge base from backup."""
    import json
    
    # Load backup data
    with open(backup_path, 'r') as f:
        backup_data = json.load(f)
    
    data = backup_data["data"]
    
    # Restore nodes
    for node_data in data["nodes"]:
        node = Node(**node_data)
        await kb.insert_node(node)
    
    # Restore edges
    for edge_data in data["edges"]:
        edge = Edge(**edge_data)
        await kb.insert_edge(edge)
    
    print("Restoration completed")
```

## Troubleshooting

### Common Issues

**High Memory Usage:**
```python
# Check memory distribution
runtime_count = await kb.count_nodes(tier="runtime")
total_count = await kb.count_nodes()
memory_pct = (runtime_count / total_count) * 100

if memory_pct > 80:
    # Trigger aggressive pruning
    await kb.prune(runtime_limit=int(total_count * 0.3))
```

**Slow Queries:**
```python
# Debug slow queries
async def debug_query_performance(kb: KnowledgeBase, **query_args):
    start = time.time()
    result = await kb.query_nodes(**query_args)
    duration = time.time() - start
    
    if duration > 0.1:  # Slower than 100ms
        print(f"Slow query detected:")
        print(f"  Query: {query_args}")
        print(f"  Duration: {duration*1000:.2f}ms")
        print(f"  Results: {len(result.nodes)}")
        print(f"  Storage tier: {result.storage_tier}")
```

### Performance Monitoring

```python
# Continuous performance monitoring
async def monitor_performance(kb: KnowledgeBase):
    """Monitor key performance indicators."""
    while True:
        try:
            # Collect metrics
            metrics = await collect_performance_metrics(kb)
            
            # Check thresholds
            if metrics["query_latency_ms"] > 100:
                print("WARNING: High query latency detected")
            
            if metrics["nodes_runtime"] > 50000:
                print("WARNING: High memory usage detected")
                await kb.prune(runtime_limit=25000)
            
            # Wait before next check
            await asyncio.sleep(60)  # Check every minute
            
        except Exception as e:
            print(f"Monitoring error: {e}")
            await asyncio.sleep(60)
```

## Production Checklist

### Pre-Deployment
- [ ] Performance benchmarks completed
- [ ] Security review completed
- [ ] Backup/restore procedures tested
- [ ] Monitoring systems configured
- [ ] Load testing completed
- [ ] Documentation updated

### Deployment
- [ ] Health checks configured
- [ ] Metrics collection enabled
- [ ] Log aggregation configured
- [ ] Alerting rules defined
- [ ] Rollback plan prepared
- [ ] Team training completed

### Post-Deployment
- [ ] Performance monitoring active
- [ ] Regular backups scheduled
- [ ] Security scanning enabled
- [ ] Capacity planning reviewed
- [ ] Incident response procedures tested
- [ ] Performance optimization ongoing