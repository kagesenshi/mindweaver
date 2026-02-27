# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import os
import subprocess
import sys
import re
from pathlib import Path


class BaseReleaser:
    """Base class for releasers with common functionality."""

    def __init__(self, dry_run=False, registry=None, chart_registry=None):
        self.dry_run = dry_run
        self.registry = registry
        self.chart_registry = chart_registry
        # Root dir is parent of releaser directory
        self.root_dir = Path(__file__).parent.parent.parent.parent.absolute()
        os.chdir(self.root_dir)

    def run_command(self, cmd, check=True, cwd=None):
        """Run a shell command and print it."""
        display_cmd = " ".join(cmd)
        if cwd:
            print(f"Executing (in {cwd}): {display_cmd}")
        else:
            print(f"Executing: {display_cmd}")

        if self.dry_run:
            print(f"  [Dry Run] Skipping: {display_cmd}")
            return True
        try:
            subprocess.run(cmd, check=check, cwd=cwd)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {e}")
            if check:
                sys.exit(1)
            return False

    def get_version(self, version_file):
        """Read current version from a version file."""
        if not os.path.exists(version_file):
            print(f"Error: {version_file} not found!")
            sys.exit(1)
        with open(version_file, "r") as f:
            return f.read().strip()

    def set_version(self, version_file, version):
        """Write version to a version file."""
        print(f"Updating {version_file} to {version} ...")
        if not self.dry_run:
            with open(version_file, "w") as f:
                # Add newline if it's a simple VERSION.txt
                f.write(version + ("\n" if version_file.endswith(".txt") else ""))

    def get_chart_version(self, chart_file):
        """Read current version from Chart.yaml."""
        if not os.path.exists(chart_file):
            print(f"Error: {chart_file} not found!")
            sys.exit(1)
        with open(chart_file, "r") as f:
            content = f.read()
            match = re.search(r"^version: (.*)", content, flags=re.MULTILINE)
            if match:
                return match.group(1).strip()
        print(f"Error: version not found in {chart_file}")
        sys.exit(1)

    def bump_version_patch(self, version_str):
        """Increment the patch component or revision number of a version string."""
        # Handle x.x.x-rev.n pattern
        rev_match = re.search(r"^(.*)-rev\.(\d+)$", version_str)
        if rev_match:
            base = rev_match.group(1)
            rev = int(rev_match.group(2))
            return f"{base}-rev.{rev + 1}"

        try:
            # Handle versions with any other suffixes or standard semantic versions
            # We split by '-' to handle things like 4.2.0-beta.1 or purely 4.2.0
            semver_base = version_str.split("-")[0]
            parts = semver_base.split(".")
            if len(parts) >= 3:
                major, minor, patch = map(int, parts[:3])
                return f"{major}.{minor}.{patch + 1}"
            elif len(parts) == 2:
                major, minor = map(int, parts)
                return f"{major}.{minor + 1}.0"
            elif len(parts) == 1:
                major = int(parts[0])
                return f"{major + 1}.0.0"
            return version_str
        except (ValueError, IndexError):
            print(
                f"Warning: Could not automatically bump version {version_str}, returning as is."
            )
            return version_str

    def update_chart(self, chart_file, version=None, app_version=None):
        """Update Chart.yaml with new version and/or appVersion."""
        if not os.path.exists(chart_file):
            print(f"Warning: {chart_file} not found, skipping chart update.")
            return

        updates = []
        if version:
            updates.append(f"version to {version}")
        if app_version:
            updates.append(f"appVersion to {app_version}")

        print(f"Updating {chart_file}: {', '.join(updates)} ...")

        if not self.dry_run:
            with open(chart_file, "r") as f:
                content = f.read()

            if version:
                content = re.sub(
                    r"^version: .*", f"version: {version}", content, flags=re.MULTILINE
                )
            if app_version:
                content = re.sub(
                    r"^appVersion: .*",
                    f'appVersion: "{app_version}"',
                    content,
                    flags=re.MULTILINE,
                )

            with open(chart_file, "w") as f:
                f.write(content)

    def update_changelog(self, changelog_file, version):
        """Update CHANGELOG.md with new version section."""
        if not os.path.exists(changelog_file):
            print(f"Warning: {changelog_file} not found, skipping changelog update.")
            return

        print(f"Updating {changelog_file} to include {version} ...")
        if not self.dry_run:
            with open(changelog_file, "r") as f:
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

            with open(changelog_file, "w") as f:
                f.writelines(new_lines)

    def git_ops(self, version_files, tag, message, commit=True):
        """Common git operations for release."""
        confirm = input(f"Commit, tag and push release {tag}? [y/N]: ").strip().lower()
        if confirm == "y":
            print("Staging changes...")
            self.run_command(["git", "add"] + version_files)

            if commit:
                print(f"Committing {message} ...")
                self.run_command(["git", "commit", "-m", message])

            print(f"Tagging {tag} ...")
            self.run_command(["git", "tag", tag])

            print("Pushing to origin...")
            self.run_command(["git", "push"])
            self.run_command(["git", "push", "--tags"])

            print("Git operations completed successfully!")
        else:
            print("Skipping Git operations.")

    def git_commit(self, files, message, push=True):
        """Commit files and optionally push."""
        print(f"Committing changes: {message} ...")
        self.run_command(["git", "add"] + files)
        self.run_command(["git", "commit", "-m", message])
        if push:
            print("Pushing to origin...")
            self.run_command(["git", "push"])
        print("Commit completed successfully!")
