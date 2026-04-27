# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
from .base import BaseReleaser

# Configuration
VERSION_FILE = "images/ranger/VERSION.txt"
CHART_FILE = "charts/ranger/Chart.yaml"
IMAGE_NAME = "ranger"
RELEASED_VERSION_FILE = "images/ranger/RELEASED_VERSION.txt"


class RangerReleaser(BaseReleaser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_image_released = None
        self.release_chart_version = None

    def prep(self, version=None):
        """Prepare release: update versions, build docker, package helm."""
        release_new_image = (
            input("Release new image version? [y/N]: ").strip().lower() == "y"
        )
        self.new_image_released = release_new_image

        current_app_version = self.get_version(VERSION_FILE)
        recommended_app_version = current_app_version.replace("-alpha", "")
        if release_new_image:
            if not version:
                version = (
                    input(
                        f"Enter app version to release [{recommended_app_version}]: "
                    ).strip()
                    or recommended_app_version
                )
            self.set_version(VERSION_FILE, version)
        else:
            version = self.get_version(RELEASED_VERSION_FILE)
            print(f"Using current app version {version} (no new image release).")

        current_chart_version = self.get_chart_version(CHART_FILE)
        recommended_chart_version = current_chart_version.replace("-alpha", "")
        new_chart_version = (
            input(
                f"Enter chart version to release [{recommended_chart_version}]: "
            ).strip()
            or recommended_chart_version
        )

        self.release_chart_version = new_chart_version
        print(
            f"Preparing Ranger release {version} (Chart: {new_chart_version}) ..."
        )
        self.update_chart(CHART_FILE, version=new_chart_version, app_version=version)

        if release_new_image:
            # Build Container Image
            image_tag = f"{self.registry}/{IMAGE_NAME}:{version}"
            latest_tag = f"{self.registry}/{IMAGE_NAME}:latest"
            print(f"Building container image {image_tag} ...")
            self.run_command(
                [
                    "docker",
                    "build",
                    "-t",
                    image_tag,
                    "-t",
                    latest_tag,
                    "-f",
                    "images/ranger/Dockerfile",
                    "images/ranger",
                ]
            )
        else:
            print("Skipping image build as requested.")

        # Build Helm Package
        if os.path.isdir("charts/ranger"):
            print("Updating Helm dependencies ...")
            self.run_command(["helm", "dependency", "update", "charts/ranger"])

            print("Packaging Helm chart ...")
            self.run_command(["helm", "package", "charts/ranger"])
        else:
            print(
                "Warning: charts/ranger directory not found, skipping helm packaging."
            )

        print(f"Successfully prepared release {version}")
        return version

    def push(self, version=None):
        """Push release: push docker images, push helm package."""
        if not version:
            version = self.get_version(VERSION_FILE)

        new_image_released = self.new_image_released
        if new_image_released is None:
            new_image_released = (
                input("Was a new image version released? [y/N]: ").strip().lower()
                == "y"
            )

        if new_image_released:
            print(f"Pushing Ranger container images for version {version} ...")
            self.run_command(
                ["docker", "push", f"{self.registry}/{IMAGE_NAME}:{version}"]
            )
            self.run_command(["docker", "push", f"{self.registry}/{IMAGE_NAME}:latest"])
        else:
            print("Skipping image push as no new image was released.")

        chart_version = self.get_chart_version(CHART_FILE)
        chart_package = f"ranger-{chart_version}.tgz"
        if os.path.exists(chart_package):
            print(f"Pushing Helm package {chart_package} to {self.chart_registry} ...")
            self.run_command(["helm", "push", chart_package, self.chart_registry])
        else:
            print(f"Warning: Helm package {chart_package} not found, skipping push.")

        print(f"Release {version} pushed successfully!")

    def post(self, version=None):
        """Post-release: git commit/tag/push current state, then bump version for next cycle."""
        if not version:
            version = self.get_version(VERSION_FILE)

        # 1. Commit and tag the release first
        current_chart_version = self.release_chart_version or self.get_chart_version(
            CHART_FILE
        )
        if self.new_image_released:
            self.set_version(RELEASED_VERSION_FILE, version)

        self.git_ops(
            version_files=[VERSION_FILE, CHART_FILE, RELEASED_VERSION_FILE],
            tag=f"{IMAGE_NAME}-v{current_chart_version}",
            message=f"release {IMAGE_NAME} {current_chart_version} (app: {version})",
        )

        # 2. Bump versions for next development cycle
        new_image_released = self.new_image_released
        if new_image_released is None:
            new_image_released = (
                input("Was a new image version released? [y/N]: ").strip().lower()
                == "y"
            )

        updated_files = [CHART_FILE]

        if new_image_released:
            recommended_next_image = self.bump_version_patch(version)
            if "-alpha" not in recommended_next_image:
                recommended_next_image = f"{recommended_next_image}-alpha"

            print(f"Current app version released: {version}")
            next_app_version = (
                input(
                    f"Enter next app development version [{recommended_next_image}]: "
                ).strip()
                or recommended_next_image
            )

            print(f"Starting next app development cycle {next_app_version} ...")
            self.set_version(VERSION_FILE, next_app_version)
            self.update_chart(CHART_FILE, app_version=next_app_version)
            updated_files.append(VERSION_FILE)
        else:
            print("Skipping image version bump as no new image was released.")

        # ALWAYS bump chart version
        current_chart_version = self.get_chart_version(CHART_FILE)
        recommended_next_chart = self.bump_version_patch(current_chart_version)
        if "-alpha" not in recommended_next_chart:
            recommended_next_chart = f"{recommended_next_chart}-alpha"

        print(f"Current chart version released: {current_chart_version}")
        next_chart_version = (
            input(
                f"Enter next chart development version [{recommended_next_chart}]: "
            ).strip()
            or recommended_next_chart
        )
        print(f"Starting next chart development cycle {next_chart_version} ...")
        self.update_chart(CHART_FILE, version=next_chart_version)

        # 3. Commit the bump
        confirm = (
            input("Commit start of next development cycle? [y/N]: ").strip().lower()
            == "y"
        )
        if confirm:
            self.git_commit(
                files=updated_files,
                message=f"bump version to chart={next_chart_version}"
                + (f", app={next_app_version}" if new_image_released else ""),
            )

    def full(self):
        """Run full release cycle."""
        version = self.prep()
        self.push(version)
        self.post(version)
