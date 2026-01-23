#!/bin/bash

# Environment activation script for LinguaSign AI
cd "$(dirname "$0")"
source venv/bin/activate

echo ""
echo "✓ Environment activated"
echo "  Python: $(python3 --version)"
echo "  Location: $(pwd)"
echo ""
echo "Ready to run:"
echo "  python3 extract_signatures.py"
echo "  python3 verify_signatures.py assets/signatures/HELLO.json --animate"
echo ""
echo "To deactivate: deactivate"
echo ""
