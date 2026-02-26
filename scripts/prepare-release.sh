#!/bin/bash
# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

set -e

# Configuration
VERSION_FILE="VERSION.txt"
CHART_FILE="helm/mindweaver/Chart.yaml"
IMAGE_NAME="mindweaver"
REGISTRY="ghcr.io/kagesenshi/mindweaver"

# 1. Version Management
if [ ! -f "$VERSION_FILE" ]; then
    echo "Error: $VERSION_FILE not found!"
    exit 1
fi

CURRENT_VERSION=$(cat "$VERSION_FILE")
NEW_VERSION=$1

if [ -z "$NEW_VERSION" ]; then
    echo "Current version: $CURRENT_VERSION"
    read -p "Enter version to release [$CURRENT_VERSION]: " NEW_VERSION
    NEW_VERSION=${NEW_VERSION:-$CURRENT_VERSION}
fi

echo "Preparing release $NEW_VERSION ..."

# Update VERSION.txt
echo "$NEW_VERSION" > "$VERSION_FILE"

# Update Chart.yaml
if [ -f "$CHART_FILE" ]; then
    echo "Updating $CHART_FILE ..."
    sed -i "s/^version: .*/version: $NEW_VERSION/" "$CHART_FILE"
    sed -i "s/^appVersion: .*/appVersion: \"$NEW_VERSION\"/" "$CHART_FILE"
else
    echo "Warning: $CHART_FILE not found, skipping chart update."
fi

# 2. Build Container Image
echo "Building container image ${REGISTRY}/${IMAGE_NAME}:${NEW_VERSION} ..."
docker build -t "${REGISTRY}/${IMAGE_NAME}:${NEW_VERSION}" -t "${REGISTRY}/${IMAGE_NAME}:latest" .

# 3. Build Helm Package
if [ -d "helm/mindweaver" ]; then
    echo "Updating Helm dependencies ..."
    helm dependency update helm/mindweaver
    
    echo "Packaging Helm chart ..."
    helm package helm/mindweaver
else
    echo "Warning: helm/mindweaver directory not found, skipping helm packaging."
fi

echo "Successfully prepared release ${NEW_VERSION}"
echo "Container images:"
echo "  - ${REGISTRY}/${IMAGE_NAME}:${NEW_VERSION}"
echo "  - ${REGISTRY}/${IMAGE_NAME}:latest"
echo "Helm package:"
ls mindweaver-${NEW_VERSION}.tgz 2>/dev/null || echo "  (Helm package not found or version mismatch)"
