#!/bin/bash

# Push Data to Cloud Script
# Run this after uploading data locally to sync with Streamlit Cloud

echo "🔄 Syncing data to cloud..."
echo ""

cd "/Users/kwokric/JIRA management"

# Check if there are changes
if git diff --quiet data/; then
    echo "ℹ️  No data changes detected."
    exit 0
fi

# Add data files
echo "📦 Adding data files..."
git add data/

# Commit with timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
git commit -m "Data update: $TIMESTAMP"

# Push to GitHub
echo "🚀 Pushing to GitHub..."
git push origin main

echo ""
echo "✅ Done! Data synced to cloud."
echo "⏱️  Streamlit Cloud will refresh in ~30 seconds."
echo ""
