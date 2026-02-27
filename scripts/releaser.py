#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import argparse
import os
import subprocess
import sys
import re
from pathlib import Path

# Configuration
VERSION_FILE = "VERSION.txt"
CHART_FILE = "helm/mindweaver/Chart.yaml"
IMAGE_NAME = "mindweaver"
REGISTRY = "ghcr.io/kagesenshi/mindweaver"
CHART_REGISTRY = "oci://ghcr.io/kagesenshi/mindweaver/charts"
CHANGELOG_FILE = "CHANGELOG.md"


class Releaser:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.root_dir = Path(__file__).parent.parent.absolute()
        os.chdir(self.root_dir)

    def run_command(self, cmd, check=True):
        """Run a shell command and print it."""
        print(f"Executing: {' '.join(cmd)}")
        if self.dry_run:
            print(f"  [Dry Run] Skipping: {' '.join(cmd)}")
            return True
        try:
            subprocess.run(cmd, check=check)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}")
            if check:
                sys.exit(1)
            return False

    def get_version(self):
        """Read current version from VERSION.txt."""
        if not os.path.exists(VERSION_FILE):
            print(f"Error: {VERSION_FILE} not found!")
            sys.exit(1)
        with open(VERSION_FILE, "r") as f:
            return f.read().strip()

    def set_version(self, version):
        """Write version to VERSION.txt."""
        print(f"Updating {VERSION_FILE} to {version} ...")
        if not self.dry_run:
            with open(VERSION_FILE, "w") as f:
                f.write(version)

    def update_chart(self, version):
        """Update Chart.yaml with new version."""
        if not os.path.exists(CHART_FILE):
            print(f"Warning: {CHART_FILE} not found, skipping chart update.")
            return

        print(f"Updating {CHART_FILE} to {version} ...")
        if not self.dry_run:
            with open(CHART_FILE, "r") as f:
                content = f.read()

            content = re.sub(
                r"^version: .*", f"version: {version}", content, flags=re.MULTILINE
            )
            content = re.sub(
                r"^appVersion: .*",
                f'appVersion: "{version}"',
                content,
                flags=re.MULTILINE,
            )

            with open(CHART_FILE, "w") as f:
                f.write(content)

    def update_changelog(self, version):
        """Update CHANGELOG.md with new version section."""
        if not os.path.exists(CHANGELOG_FILE):
            print(f"Warning: {CHANGELOG_FILE} not found, skipping changelog update.")
            return

        print(f"Updating {CHANGELOG_FILE} to include {version} ...")
        if not self.dry_run:
            with open(CHANGELOG_FILE, "r") as f:
                lines = f.readlines()

            new_lines = []
            inserted = False
            for line in lines:
                if not inserted and line.startswith("## ["):
                    new_lines.append(f"## [{version}] - Unreleased\n\n")
                    inserted = True
                new_lines.append(line)

            if not inserted:
                new_lines.insert(0, f"## [{version}] - Unreleased\n\n")

            with open(CHANGELOG_FILE, "w") as f:
                f.writelines(new_lines)

    def prep(self, version=None):
        """Prepare release: update versions, build docker, package helm."""
        current_version = self.get_version()
        if not version:
            version = (
                input(f"Enter version to release [{current_version}]: ").strip()
                or current_version
            )

        print(f"Preparing release {version} ...")
        self.set_version(version)
        self.update_chart(version)

        # Build Container Image
        image_tag = f"{REGISTRY}/{IMAGE_NAME}:{version}"
        latest_tag = f"{REGISTRY}/{IMAGE_NAME}:latest"
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
            version = self.get_version()

        print(f"Pushing container images for version {version} ...")
        self.run_command(["docker", "push", f"{REGISTRY}/{IMAGE_NAME}:{version}"])
        self.run_command(["docker", "push", f"{REGISTRY}/{IMAGE_NAME}:latest"])

        chart_package = f"mindweaver-{version}.tgz"
        if os.path.exists(chart_package):
            print(f"Pushing Helm package {chart_package} to {CHART_REGISTRY} ...")
            self.run_command(["helm", "push", chart_package, CHART_REGISTRY])
        else:
            print(f"Warning: Helm package {chart_package} not found, skipping push.")

        print(f"Release {version} pushed successfully!")

    def post(self, version=None):
        """Post-release: bump version, update files, git commit/tag/push."""
        if not version:
            version = self.get_version()

        # Calculate recommended next version
        major, minor, patch = map(int, version.split("."))
        recommended_next = f"{major}.{minor}.{patch + 1}"

        print(f"Current version released: {version}")
        next_version = (
            input(f"Enter next development version [{recommended_next}]: ").strip()
            or recommended_next
        )

        print(f"Updating to next development version {next_version} ...")
        self.set_version(next_version)
        self.update_chart(next_version)
        self.update_changelog(next_version)

        confirm = (
            input(f"Commit, tag and push release {version}? [y/N]: ").strip().lower()
        )
        if confirm == "y":
            print("Staging changes...")
            self.run_command(["git", "add", VERSION_FILE, CHART_FILE, CHANGELOG_FILE])

            print(f"Committing release {version} ...")
            self.run_command(["git", "commit", "-m", f"released {version}"])

            print(f"Tagging v{version} ...")
            self.run_command(["git", "tag", f"v{version}"])

            print("Pushing to origin...")
            self.run_command(["git", "push"])
            self.run_command(["git", "push", "--tags"])

            print("Git operations completed successfully!")
        else:
            print("Skipping Git operations.")

    def full(self):
        """Run full release cycle."""
        version = self.prep()
        self.push(version)
        self.post(version)


def main():
    parser = argparse.ArgumentParser(description="MindWeaver Releaser")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show commands without executing them"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    parser_prep = subparsers.add_parser(
        "prep", help="Prepare release (update versions, build, package)"
    )
    parser_prep.add_argument("version", nargs="?", help="Version to release")

    parser_push = subparsers.add_parser(
        "push", help="Push release (docker images, helm package)"
    )
    parser_push.add_argument("version", nargs="?", help="Version to push")

    parser_post = subparsers.add_parser(
        "post", help="Post-release actions (version bump, git ops)"
    )
    parser_post.add_argument("version", nargs="?", help="Version just released")

    subparsers.add_parser("full", help="Full release cycle (prep -> push -> post)")

    args = parser.parse_args()

    releaser = Releaser(dry_run=args.dry_run)

    if args.command == "prep":
        releaser.prep(args.version)
    elif args.command == "push":
        releaser.push(args.version)
    elif args.command == "post":
        releaser.post(args.version)
    elif args.command == "full":
        releaser.full()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
