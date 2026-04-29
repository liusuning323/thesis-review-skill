#!/bin/bash
# Phase 0 automated preflight check for LaTeX thesis
# Usage: bash preflight_check.sh thesis.tex

set -e

THESIS="${1:-thesis.tex}"

if [ ! -f "$THESIS" ]; then
    echo "ERROR: $THESIS not found"
    exit 1
fi

echo "=== Preflight Check: $THESIS ==="
echo ""

# 1. RQ consistency
echo "--- RQ Consistency ---"
RQ1_COUNT=$(grep -c "What educational purposes are articulated" "$THESIS" 2>/dev/null || echo 0)
if [ "$RQ1_COUNT" -ge 2 ]; then
    echo "✅ RQ1 found $RQ1_COUNT times (expect ≥2: Ch1 + Ch4)"
else
    echo "⚠️  RQ1 found only $RQ1_COUNT times — check Ch4 alignment"
fi

# 2. Repetition check
echo ""
echo "--- Phrase Repetition ---"
for phrase in "supplemented by related" "three domains" "three functions"; do
    COUNT=$(grep -c "$phrase" "$THESIS" 2>/dev/null || echo 0)
    if [ "$COUNT" -gt 4 ]; then
        echo "⚠️  '$phrase' appears $COUNT times (threshold: ≤4)"
    elif [ "$COUNT" -gt 0 ]; then
        echo "✅ '$phrase' appears $COUNT times"
    fi
done

# 3. Terminology drift
echo ""
echo "--- Terminology Drift ---"
FUNCTIONS=$(grep -c "three functions" "$THESIS" 2>/dev/null || echo 0)
DOMAINS=$(grep -c "three domains" "$THESIS" 2>/dev/null || echo 0)
PURPOSES=$(grep -c "three educational purposes" "$THESIS" 2>/dev/null || echo 0)
echo "  'three functions': $FUNCTIONS"
echo "  'three domains': $DOMAINS"
echo "  'three educational purposes': $PURPOSES"
if [ "$FUNCTIONS" -gt 0 ] || [ "$DOMAINS" -gt 0 ]; then
    echo "⚠️  Terminology drift detected — standardize to 'three educational purposes'"
else
    echo "✅ Terminology consistent"
fi

# 4. PRISMA numbers
echo ""
echo "--- PRISMA Numbers ---"
PRISMA_ID=$(grep -oP '\\PRISMAIdentified\{\d+\}' "$THESIS" 2>/dev/null | grep -oP '\d+' || echo "N/A")
echo "  PRISMA identified (macro): $PRISMA_ID"
# Check for common error
if grep -q "2,354" "$THESIS" 2>/dev/null; then
    echo "🔴 ERROR: Found '2,354' — should be 894 or PRISMA macro"
fi

# 5. Image file sizes
echo ""
echo "--- Image Files ---"
for img in $(grep -oP 'includegraphics[^}]*\{([^}]+)\}' "$THESIS" 2>/dev/null | grep -oP '\{[^}]+\}' | tr -d '{}'); do
    if [ -f "$img" ]; then
        SIZE=$(stat -f%z "$img" 2>/dev/null || stat -c%s "$img" 2>/dev/null)
        if [ "$SIZE" -lt 10000 ]; then
            echo "⚠️  $img: ${SIZE} bytes — may be placeholder (threshold: 10KB)"
        else
            echo "✅ $img: ${SIZE} bytes"
        fi
    else
        echo "❌ $img: FILE MISSING"
    fi
done

# 6. Chinese font support
echo ""
echo "--- CJK Font Support ---"
if grep -q "xeCJK\|ctex\|CJK" "$THESIS" 2>/dev/null; then
    echo "✅ CJK package detected (xeCJK/ctex/CJK)"
else
    CHINESE_CHARS=$(grep -oP '[\x{4e00}-\x{9fff}]' "$THESIS" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$CHINESE_CHARS" -gt 0 ]; then
        echo "🔴 ERROR: $CHINESE_CHARS Chinese characters found but NO CJK font package"
    else
        echo "✅ No Chinese characters detected — CJK package not needed"
    fi
fi

echo ""
echo "=== Preflight Complete ==="
