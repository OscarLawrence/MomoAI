# Momo Logger Benchmarks

Performance benchmarks for the momo-logger module.

## Benchmark Scripts

- `basic_performance.py` - Measures basic logging performance across different levels, backends, and formatters
- `concurrent_performance.py` - Measures performance under concurrent load simulating multi-agent systems

## Running Benchmarks

```bash
# List all available benchmarks
pdm run list-benchmarks

# Run a specific benchmark
pdm run benchmark-basic
pdm run benchmark-concurrent

# Run a specific benchmark by name
pdm run benchmark basic_performance
pdm run benchmark concurrent_performance
```

## Performance Characteristics

The momo-logger is designed for high-performance applications with the following characteristics:

- **Buffer Backend**: 250,000+ messages/second
- **Console Backend**: 100,000+ messages/second
- **File Backend**: 120,000+ messages/second
- **Context Management**: Minimal overhead (< 5% in most cases)
- **Concurrent Logging**: Scales well with multiple loggers and writers

## Key Performance Features

1. **Zero Blocking**: Async-first design ensures no blocking operations
2. **Minimal Allocation**: Efficient object reuse and minimal memory allocation
3. **Fast Formatting**: Optimized formatters for different output formats
4. **Context Efficiency**: Smart context management with low overhead
5. **Backend Optimization**: Each backend optimized for its specific use case