# SPDX-FileCopyrightText: Copyright © 2026 Mohd Izhar Firdaus Bin Ismail
# SPDX-License-Identifier: AGPLv3+

import click
from .mindweaver import MindWeaverReleaser
from .hms import HMSReleaser


@click.group()
@click.option("--dry-run", is_flag=True, help="Show commands without executing them")
@click.option("--registry", help="Alternative image registry URL")
@click.option("--chart-registry", help="Alternative Helm chart registry URL (OCI)")
@click.pass_context
def cli(ctx, dry_run, registry, chart_registry):
    """MindWeaver Releaser CLI"""
    from .settings import settings

    ctx.ensure_object(dict)
    ctx.obj["dry_run"] = dry_run
    ctx.obj["registry"] = registry or settings.registry
    ctx.obj["chart_registry"] = chart_registry or settings.chart_registry


@cli.group()
def mindweaver():
    """MindWeaver core application release commands"""
    pass


@cli.group()
def hms():
    """Hive Metastore release commands"""
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
        )
        releaser.full()


create_command(mindweaver, MindWeaverReleaser)
create_command(hms, HMSReleaser)


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
