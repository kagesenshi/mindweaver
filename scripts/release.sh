#!/bin/bash
# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

set -e

# Configuration
VERSION_FILE="VERSION.txt"
CHART_FILE="helm/mindweaver/Chart.yaml"
IMAGE_NAME="mindweaver"
REGISTRY="ghcr.io/kagesenshi/mindweaver"
CHART_REGISTRY="oci://ghcr.io/kagesenshi/mindweaver/charts"

if [ ! -f "$VERSION_FILE" ]; then
    echo "Error: $VERSION_FILE not found!"
    exit 1
fi

VERSION=$(cat "$VERSION_FILE")

# 1. Push Container Images
echo "Pushing container images for version $VERSION ..."
docker push "${REGISTRY}/${IMAGE_NAME}:${VERSION}"
docker push "${REGISTRY}/${IMAGE_NAME}:latest"

# 2. Push Helm Package
CHART_PACKAGE="mindweaver-${VERSION}.tgz"
if [ -f "$CHART_PACKAGE" ]; then
    echo "Pushing Helm package $CHART_PACKAGE to $CHART_REGISTRY ..."
    helm push "$CHART_PACKAGE" "$CHART_REGISTRY"
else
    echo "Warning: Helm package $CHART_PACKAGE not found, skipping push."
fi

echo "Relase $VERSION pushed successfully!"

# 3. Post-Release Version Bump
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

echo "Successfully updated to $NEXT_VERSION"
