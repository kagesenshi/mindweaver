# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
from .base import BaseReleaser

# Configuration
VERSION_FILE = "images/trino/VERSION.txt"
IMAGE_NAME = "trino"
RELEASED_VERSION_FILE = "images/trino/RELEASED_VERSION.txt"


class TrinoReleaser(BaseReleaser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.new_image_released = None

    def prep(self, version=None):
        """Prepare release: update versions, build docker."""
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

        print(f"Preparing Trino release {version} ...")

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
                    "images/trino/Dockerfile",
                    "images/trino",
                ]
            )
        else:
            print("Skipping image build as requested.")

        print(f"Successfully prepared release {version}")
        return version

    def push(self, version=None):
        """Push release: push docker images."""
        if not version:
            version = self.get_version(VERSION_FILE)

        new_image_released = self.new_image_released
        if new_image_released is None:
            new_image_released = self.confirm("Was a new image version released? [y/N]: ", default=False)

        if new_image_released:
            print(f"Pushing Trino container images for version {version} ...")
            self.run_command(
                ["docker", "push", f"{self.registry}/{IMAGE_NAME}:{version}"]
            )
            self.run_command(["docker", "push", f"{self.registry}/{IMAGE_NAME}:latest"])
        else:
            print("Skipping image push as no new image was released.")

        print(f"Release {version} pushed successfully!")

    def post(self, version=None):
        """Post-release: git commit/tag/push current state, then bump version for next cycle."""
        if not version:
            version = self.get_version(VERSION_FILE)

        # 1. Commit and tag the release first
        if self.new_image_released:
            self.set_version(RELEASED_VERSION_FILE, version)

        self.git_ops(
            version_files=[VERSION_FILE, RELEASED_VERSION_FILE],
            tag=f"{IMAGE_NAME}-v{version}",
            message=f"release {IMAGE_NAME} {version}",
        )

        # 2. Bump versions for next development cycle
        new_image_released = self.new_image_released
        if new_image_released is None:
            new_image_released = self.confirm("Was a new image version released? [y/N]: ", default=False)

        updated_files = []

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
            updated_files.append(VERSION_FILE)
        else:
            print("Skipping image version bump as no new image was released.")

        # 3. Commit the bump
        if updated_files:
            confirm = self.confirm("Commit start of next development cycle? [y/N]: ", default=False, is_git=True)
            if confirm:
                self.git_commit(
                    files=updated_files,
                    message=f"bump version to app={next_app_version}",
                )

    def full(self):
        """Run full release cycle."""
        version = self.prep()
        self.push(version)
        self.post(version)
