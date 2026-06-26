# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import click
from .mindweaver import MindWeaverReleaser
from .hms import HMSReleaser
from .ranger import RangerReleaser
from .superset import SupersetReleaser
from .trino import TrinoReleaser
from .airflow import AirflowReleaser
from .nifi import NifiReleaser


@click.group()
@click.option("--dry-run", is_flag=True, help="Show commands without executing them")
@click.option("--registry", help="Alternative image registry URL")
@click.option("--chart-registry", help="Alternative Helm chart registry URL (OCI)")
@click.option("-y", "--yes", is_flag=True, help="Run in unattended mode (auto-confirm all prompts)")
@click.option("--auto-tag-and-push", is_flag=True, help="Auto-confirm Git commit/tag/push operations")
@click.pass_context
def cli(ctx, dry_run, registry, chart_registry, yes, auto_tag_and_push):
    """MindWeaver Releaser CLI"""
    from .settings import settings

    ctx.ensure_object(dict)
    ctx.obj["dry_run"] = dry_run
    ctx.obj["registry"] = registry or settings.registry
    ctx.obj["chart_registry"] = chart_registry or settings.chart_registry
    ctx.obj["yes"] = yes
    ctx.obj["auto_tag_and_push"] = auto_tag_and_push


@cli.group()
def mindweaver():
    """MindWeaver core application release commands"""
    pass


@cli.group()
def hms():
    """Hive Metastore release commands"""
    pass


@cli.group()
def superset():
    """Superset release commands"""
    pass


@cli.group()
def ranger():
    """Ranger release commands"""
    pass


@cli.group()
def trino():
    """Trino release commands"""
    pass


@cli.group()
def airflow():
    """Apache Airflow release commands"""
    pass


@cli.group()
def nifi():
    """NiFi release commands"""
    pass


def create_command(group, releaser_class):
    @group.command()
    @click.argument("version", required=False)
    @click.pass_context
    def prep(ctx, version):
        """Prepare release (update versions, build, package)"""
        releaser = releaser_class(
            dry_run=ctx.obj["dry_run"],
            registry=ctx.obj["registry"],
            chart_registry=ctx.obj["chart_registry"],
            yes=ctx.obj.get("yes", False),
            auto_tag_and_push=ctx.obj.get("auto_tag_and_push", False),
        )
        releaser.prep(version)

    @group.command()
    @click.argument("version", required=False)
    @click.pass_context
    def push(ctx, version):
        """Push release (docker images, helm package)"""
        releaser = releaser_class(
            dry_run=ctx.obj["dry_run"],
            registry=ctx.obj["registry"],
            chart_registry=ctx.obj["chart_registry"],
            yes=ctx.obj.get("yes", False),
            auto_tag_and_push=ctx.obj.get("auto_tag_and_push", False),
        )
        releaser.push(version)

    @group.command()
    @click.argument("version", required=False)
    @click.pass_context
    def post(ctx, version):
        """Post-release actions (version bump, git ops)"""
        releaser = releaser_class(
            dry_run=ctx.obj["dry_run"],
            registry=ctx.obj["registry"],
            chart_registry=ctx.obj["chart_registry"],
            yes=ctx.obj.get("yes", False),
            auto_tag_and_push=ctx.obj.get("auto_tag_and_push", False),
        )
        releaser.post(version)

    @group.command()
    @click.pass_context
    def full(ctx):
        """Full release cycle (prep -> push -> post)"""
        releaser = releaser_class(
            dry_run=ctx.obj["dry_run"],
            registry=ctx.obj["registry"],
            chart_registry=ctx.obj["chart_registry"],
            yes=ctx.obj.get("yes", False),
            auto_tag_and_push=ctx.obj.get("auto_tag_and_push", False),
        )
        releaser.full()


create_command(mindweaver, MindWeaverReleaser)
create_command(hms, HMSReleaser)
create_command(superset, SupersetReleaser)
create_command(ranger, RangerReleaser)
create_command(trino, TrinoReleaser)
create_command(airflow, AirflowReleaser)
create_command(nifi, NifiReleaser)


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
