#!/bin/bash
# Test shell script for Mom execution demo
# Shows how Mom can execute bash scripts with arguments

echo "🐚 Shell Script Execution Test"
echo "Script: $0"
echo "Arguments: $@"
echo "Working directory: $(pwd)"
echo "Environment variable TEST_VAR: ${TEST_VAR:-'not set'}"

# Test some shell features
echo "Available commands:"
echo "  - ls: $(which ls)"
echo "  - python: $(which python || echo 'not found')"
echo "  - node: $(which node || echo 'not found')"

echo "✅ Shell script executed successfully!"