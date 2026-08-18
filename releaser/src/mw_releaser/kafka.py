# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

"""Kafka releaser module."""

import os
from .base import BaseReleaser

# Configuration
VERSION_FILE = "images/kafka/VERSION.txt"
CHART_FILE = "charts/kafka/Chart.yaml"
IMAGE_NAME = "kafka"
RELEASED_VERSION_FILE = "images/kafka/RELEASED_VERSION.txt"


class KafkaReleaser(BaseReleaser):
    """Releaser class for Kafka charts and container images."""

    def __init__(self, *args, **kwargs):
        """Initialize KafkaReleaser."""
        super().__init__(*args, **kwargs)
        self.new_image_released = None
        self.release_chart_version = None

    def prep(self, version=None):
        """Prepare release: update versions, build docker, package helm."""
        release_new_image = self.confirm("Release new image version? [y/N]: ", default=False)
        self.new_image_released = release_new_image

        current_app_version = self.get_version(VERSION_FILE)
        recommended_app_version = current_app_version.replace("-alpha", "")
        if release_new_image:
            if not version:
                version = self.prompt(
                    f"Enter app version to release [{recommended_app_version}]: ",
                    default=recommended_app_version
                )
            self.set_version(VERSION_FILE, version)
        else:
            version = self.get_version(RELEASED_VERSION_FILE)
            print(f"Using current app version {version} (no new image release).")

        current_chart_version = self.get_chart_version(CHART_FILE)
        recommended_chart_version = current_chart_version.replace("-alpha", "")
        new_chart_version = self.prompt(
            f"Enter chart version to release [{recommended_chart_version}]: ",
            default=recommended_chart_version
        )

        self.release_chart_version = new_chart_version
        print(
            f"Preparing Kafka release {version} (Chart: {new_chart_version}) ..."
        )
        self.update_chart(CHART_FILE, version=new_chart_version, app_version=version)
        self.update_values_yaml("charts/kafka/values.yaml", version)

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
                    "images/kafka/Dockerfile",
                    "images/kafka",
                ]
            )
        else:
            print("Skipping image build as requested.")

        # Build Helm Package
        if os.path.isdir("charts/kafka"):
            print("Updating Helm dependencies ...")
            self.run_command(["helm", "dependency", "update", "charts/kafka"])

            print("Packaging Helm chart ...")
            self.run_command(["helm", "package", "charts/kafka"])
        else:
            print(
                "Warning: charts/kafka directory not found, skipping helm packaging."
            )

        print(f"Successfully prepared release {version}")
        return version

    def push(self, version=None):
        """Push release: push docker images, push helm package."""
        if not version:
            version = self.get_version(VERSION_FILE)

        new_image_released = self.new_image_released
        if new_image_released is None:
            new_image_released = self.confirm("Was a new image version released? [y/N]: ", default=False)

        if new_image_released:
            print(f"Pushing Kafka container images for version {version} ...")
            self.run_command(
                ["docker", "push", f"{self.registry}/{IMAGE_NAME}:{version}"]
            )
            self.run_command(["docker", "push", f"{self.registry}/{IMAGE_NAME}:latest"])
        else:
            print("Skipping image push as no new image was released.")

        chart_version = self.get_chart_version(CHART_FILE)
        chart_package = f"kafka-{chart_version}.tgz"
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
        # Tag follows chart version
        current_chart_version = self.release_chart_version or self.get_chart_version(
            CHART_FILE
        )
        if self.new_image_released:
            self.set_version(RELEASED_VERSION_FILE, version)

        self.git_ops(
            version_files=[VERSION_FILE, CHART_FILE, RELEASED_VERSION_FILE, "charts/kafka/values.yaml"],
            tag=f"{IMAGE_NAME}-v{current_chart_version}",
            message=f"release {IMAGE_NAME} {current_chart_version} (app: {version})",
        )

        # 2. Bump versions for next development cycle
        new_image_released = self.new_image_released
        if new_image_released is None:
            new_image_released = self.confirm("Was a new image version released? [y/N]: ", default=False)

        updated_files = [CHART_FILE]

        if new_image_released:
            # Calculate recommended next image version
            recommended_next_image = self.bump_version_patch(version)
            if "-alpha" not in recommended_next_image:
                recommended_next_image = f"{recommended_next_image}-alpha"

            print(f"Current app version released: {version}")
            next_app_version = self.prompt(
                f"Enter next app development version [{recommended_next_image}]: ",
                default=recommended_next_image
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
        next_chart_version = self.prompt(
            f"Enter next chart development version [{recommended_next_chart}]: ",
            default=recommended_next_chart
        )
        print(f"Starting next chart development cycle {next_chart_version} ...")
        self.update_chart(CHART_FILE, version=next_chart_version)

        # 3. Commit the bump
        confirm = self.confirm("Commit start of next development cycle? [y/N]: ", default=False, is_git=True)
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
