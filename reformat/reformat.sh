#!/bin/bash
set -e

echo ""
echo "=========================================="
echo "Running Black (code formatter)..."
echo "=========================================="
black src/

echo ""
echo "=========================================="
echo "Running docformatter (docstring formatter)..."
echo "=========================================="
docformatter \
  --in-place \
  --recursive \
  --wrap-summaries 72 \
  --wrap-descriptions 72 \
  src/ || true

echo ""
echo "=========================================="
echo "Running isort (import sorter)..."
echo "=========================================="
isort src/

echo ""
echo "=========================================="
echo "Formatting complete!"
echo "=========================================="
