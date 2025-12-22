#!/bin/bash
# Fix Line Endings Script
# Converts Windows line endings (CRLF) to Unix line endings (LF)
# Usage: ./fix-line-endings.sh [file1] [file2] ...

set -e

if [ $# -eq 0 ]; then
    echo "Usage: ./fix-line-endings.sh <file1> [file2] ..."
    echo "Example: ./fix-line-endings.sh .env.local"
    exit 1
fi

for file in "$@"; do
    if [ ! -f "$file" ]; then
        echo "⚠️  File not found: $file"
        continue
    fi
    
    echo "🔧 Fixing line endings in: $file"
    
    # Backup original
    cp "$file" "$file.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Convert CRLF to LF
    sed -i 's/\r$//' "$file"
    # OR use dos2unix if available
    # dos2unix "$file" 2>/dev/null || sed -i 's/\r$//' "$file"
    
    echo "✅ Fixed: $file"
done

echo ""
echo "✅ All files processed!"

