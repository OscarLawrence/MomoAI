# KB Playground Industry Comparison Report

Generated: 2025-08-11 14:38:06

## Overall Performance

- **Average Insertion Speed**: 525 docs/sec
- **Average Search Latency**: 112.93ms
- **Average Memory Usage**: 672.04 KB/doc
- **Datasets Tested**: 5

## Industry Comparisons

| System | Insertion Speedup | Search Speedup | Memory Efficiency |
|--------|------------------|----------------|------------------|
| Elasticsearch | 0.10x | 0.44x | 0.00x |
| Neo4J | 0.52x | 0.89x | 0.00x |
| Weaviate | 0.26x | 0.18x | 0.01x |
| Pinecone | 0.17x | 0.13x | 0.01x |

## Dataset-Specific Results

### 20Newsgroups

- **Description**: 20 Newsgroups text classification dataset
- **Size**: 957 documents
- **Domain**: general_text

- **Insertion Speed**: 22 docs/sec
- **Search Latency**: 11.53ms avg
- **Search Quality**: 0.650 avg score
- **Memory Usage**: 295.83 KB/doc
- **Relationships**: 193 discovered

### Reuters

- **Description**: Reuters-style financial news dataset
- **Size**: 500 documents
- **Domain**: financial_news

- **Insertion Speed**: 446 docs/sec
- **Search Latency**: 386.91ms avg
- **Search Quality**: 1.000 avg score
- **Memory Usage**: 483.68 KB/doc
- **Relationships**: 4340 discovered

### Wikipedia

- **Description**: Wikipedia-style encyclopedia articles
- **Size**: 300 documents
- **Domain**: encyclopedia

- **Insertion Speed**: 646 docs/sec
- **Search Latency**: 78.17ms avg
- **Search Quality**: 0.833 avg score
- **Memory Usage**: 778.49 KB/doc
- **Relationships**: 2175 discovered

### Arxiv

- **Description**: ArXiv-style scientific paper abstracts
- **Size**: 225 documents
- **Domain**: scientific_papers

- **Insertion Speed**: 822 docs/sec
- **Search Latency**: 38.82ms avg
- **Search Quality**: 0.833 avg score
- **Memory Usage**: 1023.47 KB/doc
- **Relationships**: 1425 discovered

### Stackoverflow

- **Description**: Stack Overflow-style Q&A dataset
- **Size**: 300 documents
- **Domain**: programming_qa

- **Insertion Speed**: 688 docs/sec
- **Search Latency**: 49.20ms avg
- **Search Quality**: 0.500 avg score
- **Memory Usage**: 778.71 KB/doc
- **Relationships**: 2230 discovered

