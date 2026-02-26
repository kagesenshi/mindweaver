#!/bin/bash
# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

set -e

echo "Starting full release process..."

# 1. Prepare Release
echo "Step 1: Preparing release..."
./scripts/prepare-release.sh

# 2. Release (Push)
echo "Step 2: Pushing release..."
./scripts/release.sh

# 3. Post-Release
echo "Step 3: Post-release version bump..."
./scripts/post-release.sh

echo "Full release process completed successfully!"
