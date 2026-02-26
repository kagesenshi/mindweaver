#!/bin/bash
# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

set -e

# Configuration
VERSION_FILE="VERSION.txt"
CHART_FILE="helm/mindweaver/Chart.yaml"
CHANGELOG_FILE="CHANGELOG.md"

if [ ! -f "$VERSION_FILE" ]; then
    echo "Error: $VERSION_FILE not found!"
    exit 1
fi

VERSION=$(cat "$VERSION_FILE")

# Post-Release Version Bump
# Extract major.minor.patch
IFS='.' read -r major minor patch <<< "$VERSION"
NEXT_PATCH=$((patch + 1))
RECOMMENDED_NEXT_VERSION="${major}.${minor}.${NEXT_PATCH}"

echo ""
echo "Current version released: $VERSION"
read -p "Enter next development version [$RECOMMENDED_NEXT_VERSION]: " NEXT_VERSION
NEXT_VERSION=${NEXT_VERSION:-$RECOMMENDED_NEXT_VERSION}

echo "Updating to next development version $NEXT_VERSION ..."

# Update VERSION.txt
echo "$NEXT_VERSION" > "$VERSION_FILE"

# Update Chart.yaml
if [ -f "$CHART_FILE" ]; then
    echo "Updating $CHART_FILE to $NEXT_VERSION ..."
    sed -i "s/^version: .*/version: $NEXT_VERSION/" "$CHART_FILE"
    sed -i "s/^appVersion: .*/appVersion: \"$NEXT_VERSION\"/" "$CHART_FILE"
fi

# Update CHANGELOG.md
if [ -f "$CHANGELOG_FILE" ]; then
    echo "Updating $CHANGELOG_FILE to include $NEXT_VERSION ..."
    # Insert the new version section before the first existing version header
    sed -i "0,/^## \[/s/^## \[/## [$NEXT_VERSION] - Unreleased\n\n&/" "$CHANGELOG_FILE"
fi

echo "Successfully updated to $NEXT_VERSION"

# Git Integration
echo ""
read -p "Commit, tag and push release ${VERSION}? [y/N]: " CONFIRM_GIT
if [[ "$CONFIRM_GIT" =~ ^[Yy]$ ]]; then
    echo "Staging changes..."
    git add "$VERSION_FILE" "$CHART_FILE" "$CHANGELOG_FILE"
    
    echo "Committing release $VERSION ..."
    git commit -m "released $VERSION"
    
    echo "Tagging v$VERSION ..."
    git tag "v$VERSION"
    
    echo "Pushing to origin..."
    git push
    git push --tags
    
    echo "Git operations completed successfully!"
else
    echo "Skipping Git operations."
fi
