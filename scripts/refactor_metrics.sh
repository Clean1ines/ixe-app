#!/bin/bash
echo "=== REFACTORING PROGRESS METRICS ==="
echo "Critical Methods (C):"
radon cc src/ -s | grep "C " | wc -l
echo "High Methods (B):"  
radon cc src/ -s | grep "B " | wc -l
echo "--- Top 10 Most Complex ---"
radon cc src/ -s | grep -E "(C |B )" | head -10
