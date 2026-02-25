---
name: MindWeaver Packaging
description: Guide for Helm and container image packaging rules, versioning, and tagging strategy in MindWeaver.
---
# MindWeaver Packaging

This document outlines the conventions and standards for packaging MindWeaver container images and Helm charts.

## Versioning Strategy

MindWeaver uses a decentralized versioning strategy based on `VERSION.txt` files.

1.  **Project Root `VERSION.txt`**:
    *   **Scope**: Primary application (MindWeaver backend/frontend) and the main `helm/mindweaver` chart.
    *   **Location**: `/VERSION.txt`

2.  **Component-Specific `VERSION.txt`**:
    *   **Scope**: Independent images or charts (e.g., Hive Metastore).
    *   **Location**: Inside the component directory (e.g., `images/hive-metastore/VERSION.txt`).

### Version Extraction in Workflows

To extract the version in a GitHub Action:

```yaml
      - name: Extract version
        run: echo "VERSION=$(cat path/to/VERSION.txt)" >> $GITHUB_ENV
```

## Container Image Packaging

### Base Image Tagging

All container images must be tagged with the following scheme:

*   **Stable Releases** (from git tags `v*`):
    *   `latest`: The most recent stable release.
    *   `${VERSION}`: The specific version (e.g., `0.1.0`).
*   **Development Builds** (on push to `main` branch):
    *   `edge`: The most recent build from the `main` branch (non-stable).
    *   `${GITHUB_SHA}`: A unique tag for the specific commit.
    *   `${VERSION}-alpha.${TIMESTAMP}`: A semver-compliant development version.

> [!NOTE]
> In SemVer 2.0.0, pre-release tags are sorted lexicographically (`alpha` < `beta` < `rc`). Using `alpha` ensure development builds are considered "older" than subsequent milestone releases. The `${TIMESTAMP}` suffix (e.g., `YYYYMMDDHHMMSS`) ensures uniqueness and time-ordering.

### Dockerfile Location

*   **Main App**: Root `/Dockerfile` (multi-stage).
*   **Other Images**: Subdirectories in `/images/` (e.g., `/images/hive-metastore/Dockerfile`).

### Build Configuration

Use `docker/build-push-action@v5` with GHA caching:

```yaml
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: . # or component path
          file: path/to/Dockerfile
          push: true
          tags: |
            ghcr.io/${{ github.repository_owner }}/mindweaver/<image-name>:edge
            ghcr.io/${{ github.repository_owner }}/mindweaver/<image-name>:${{ github.sha }}
            ghcr.io/${{ github.repository_owner }}/mindweaver/<image-name>:${{ env.VERSION }}-alpha.${{ env.TIMESTAMP }}

          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## Helm Chart Packaging

### Packaging Steps

1.  **Update Dependencies**: Always run `helm dependency update` before packaging.
2.  **Explicit Versioning**: Use the version extracted from the appropriate `VERSION.txt`.
3.  **Timestamp suffix**: Generate a timestamp (e.g., `date +%Y%m%d%H%M%S`) to use as a suffix for uniqueness.
4.  **App Version alignment**: Always set `--app-version` to match the chart `--version`.

```bash
VERSION=$(cat VERSION.txt)
TIMESTAMP=$(date +%Y%m%d%H%M%S)
helm package [CHART_PATH] --version "${VERSION}-alpha.${TIMESTAMP}" --app-version "${VERSION}-alpha.${TIMESTAMP}"
```


### Registry

Helm charts are pushed to the GitHub Container Registry (GHCR) as OCI artifacts:

*   **Registry URL**: `oci://ghcr.io/${{ github.repository_owner }}/mindweaver/charts`

### Workflow Example

```yaml
      - name: Package Helm chart
        run: |
          VERSION=$(cat path/to/VERSION.txt)
          TIMESTAMP=$(date +%Y%m%d%H%M%S)
          cd helm/<chart-name>
          helm package . --version "${VERSION}-alpha.${TIMESTAMP}" --app-version "${VERSION}-alpha.${TIMESTAMP}"


      - name: Push Helm chart to GHCR
        run: |
          cd helm/<chart-name>
          CHART_PACKAGE=$(ls <chart-name>-*.tgz)
          helm push "$CHART_PACKAGE" oci://ghcr.io/${{ github.repository_owner }}/mindweaver/charts
```

## Workflow Lifecycle

*   **Triggers**: Workflows should trigger on `push` and `pull_request` to the `main` branch.
*   **Path Filtering**: Use the `paths` filter to ensure workflows only run when relevant files change.
    *   Example: `paths: ["helm/mindweaver/**", "VERSION.txt"]`
