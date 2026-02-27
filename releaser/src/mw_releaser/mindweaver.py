# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
from .base import BaseReleaser

# Configuration
VERSION_FILE = "VERSION.txt"
CHART_FILE = "helm/mindweaver/Chart.yaml"
IMAGE_NAME = "mindweaver"
CHANGELOG_FILE = "CHANGELOG.md"


class MindWeaverReleaser(BaseReleaser):
    def prep(self, version=None):
        """Prepare release: update versions, build docker, package helm."""
        current_app_version = self.get_version(VERSION_FILE)
        if not version:
            version = (
                input(f"Enter app version to release [{current_app_version}]: ").strip()
                or current_app_version
            )

        current_chart_version = self.get_chart_version(CHART_FILE)
        recommended_chart_version = self.bump_version_patch(current_chart_version)
        new_chart_version = (
            input(
                f"Enter chart version to release [{recommended_chart_version}]: "
            ).strip()
            or recommended_chart_version
        )

        print(
            f"Preparing MindWeaver release {version} (Chart: {new_chart_version}) ..."
        )
        self.set_version(VERSION_FILE, version)
        self.update_chart(CHART_FILE, version=new_chart_version, app_version=version)

        # Build Container Image
        image_tag = f"{self.registry}/{IMAGE_NAME}:{version}"
        latest_tag = f"{self.registry}/{IMAGE_NAME}:latest"
        print(f"Building container image {image_tag} ...")
        self.run_command(["docker", "build", "-t", image_tag, "-t", latest_tag, "."])

        # Build Helm Package
        if os.path.isdir("helm/mindweaver"):
            print("Updating Helm dependencies ...")
            self.run_command(["helm", "dependency", "update", "helm/mindweaver"])

            print("Packaging Helm chart ...")
            self.run_command(["helm", "package", "helm/mindweaver"])
        else:
            print(
                "Warning: helm/mindweaver directory not found, skipping helm packaging."
            )

        print(f"Successfully prepared release {version}")
        return version

    def push(self, version=None):
        """Push release: push docker images, push helm package."""
        if not version:
            version = self.get_version(VERSION_FILE)

        print(f"Pushing MindWeaver container images for version {version} ...")
        self.run_command(["docker", "push", f"{self.registry}/{IMAGE_NAME}:{version}"])
        self.run_command(["docker", "push", f"{self.registry}/{IMAGE_NAME}:latest"])

        chart_package = f"mindweaver-{version}.tgz"
        if os.path.exists(chart_package):
            print(f"Pushing Helm package {chart_package} to {self.chart_registry} ...")
            self.run_command(["helm", "push", chart_package, self.chart_registry])
        else:
            print(f"Warning: Helm package {chart_package} not found, skipping push.")

        print(f"Release {version} pushed successfully!")

    def post(self, version=None):
        """Post-release: bump version, update files, git commit/tag/push."""
        if not version:
            version = self.get_version(VERSION_FILE)

        # Calculate recommended next version
        recommended_next = self.bump_version_patch(version)

        print(f"Current version released: {version}")
        next_version = (
            input(f"Enter next development version [{recommended_next}]: ").strip()
            or recommended_next
        )

        print(f"Updating to next development version {next_version} ...")
        self.set_version(VERSION_FILE, next_version)
        # In post-release, we update appVersion for next development,
        # but chart version usually stays at released version or moves to a dev suffix
        # Based on "update appVersion in chart.yml", we definitely update appVersion
        self.update_chart(CHART_FILE, app_version=next_version)
        self.update_changelog(CHANGELOG_FILE, next_version)

        self.git_ops(
            version_files=[VERSION_FILE, CHART_FILE, CHANGELOG_FILE],
            tag=f"v{version}",
            message=f"released {version}",
        )

    def full(self):
        """Run full release cycle."""
        version = self.prep()
        self.push(version)
        self.post(version)
