# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
from .base import BaseReleaser

# Configuration
VERSION_FILE = "images/hive-metastore/VERSION.txt"
CHART_FILE = "helm/hive-metastore/Chart.yaml"
IMAGE_NAME = "hive-metastore"


class HMSReleaser(BaseReleaser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_image_released = None
        self.release_chart_version = None

    def prep(self, version=None):
        """Prepare release: download deps, update versions, build docker, package helm."""
        release_new_image = (
            input("Release new image version? [y/N]: ").strip().lower() == "y"
        )
        self.new_image_released = release_new_image

        current_app_version = self.get_version(VERSION_FILE)
        if release_new_image:
            if not version:
                version = (
                    input(
                        f"Enter app version to release [{current_app_version}]: "
                    ).strip()
                    or current_app_version
                )
            self.set_version(VERSION_FILE, version)
        else:
            version = current_app_version
            print(f"Using current app version {version} (no new image release).")

        current_chart_version = self.get_chart_version(CHART_FILE)
        recommended_chart_version = self.bump_version_patch(current_chart_version)
        new_chart_version = (
            input(
                f"Enter chart version to release [{recommended_chart_version}]: "
            ).strip()
            or recommended_chart_version
        )

        self.release_chart_version = new_chart_version
        print(
            f"Preparing Hive Metastore release {version} (Chart: {new_chart_version}) ..."
        )
        self.update_chart(CHART_FILE, version=new_chart_version, app_version=version)

        if release_new_image:
            # Download external dependencies
            print("Downloading external dependencies ...")
            self.run_command(["chmod", "+x", "images/hive-metastore/download.sh"])
            self.run_command(["./download.sh"], cwd="images/hive-metastore")

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
                    "images/hive-metastore/Dockerfile",
                    "images/hive-metastore",
                ]
            )
        else:
            print("Skipping image build as requested.")

        # Build Helm Package
        if os.path.isdir("helm/hive-metastore"):
            print("Updating Helm dependencies ...")
            self.run_command(["helm", "dependency", "update", "helm/hive-metastore"])

            print("Packaging Helm chart ...")
            self.run_command(["helm", "package", "helm/hive-metastore"])
        else:
            print(
                "Warning: helm/hive-metastore directory not found, skipping helm packaging."
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
            print(f"Pushing Hive Metastore container images for version {version} ...")
            self.run_command(
                ["docker", "push", f"{self.registry}/{IMAGE_NAME}:{version}"]
            )
            self.run_command(["docker", "push", f"{self.registry}/{IMAGE_NAME}:latest"])
        else:
            print("Skipping image push as no new image was released.")

        chart_package = f"hive-metastore-{version}.tgz"
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
        self.git_ops(
            version_files=[VERSION_FILE, CHART_FILE],
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
            # Calculate recommended next image version
            recommended_next_image = self.bump_version_patch(version)

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
        if confirm == "y":
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
