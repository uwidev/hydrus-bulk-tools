#!/bin/env python

from typing import Optional
import tools
import typer
import tomllib
from typing_extensions import Annotated

app: typer.Typer = typer.Typer()

config_pth = "./config.toml"
with open(config_pth, "rb") as fp:
	config: dict = tomllib.load(fp)


@app.command(
	short_help="Attempt to create anchors for unknown urls",
	help="""
	Using your configuration defined `anchor_name`, attempts to pull relevant
	tag information from Hydrus to satisfy anchor formatting. Successfully
	created anchors will be put together into a SQLite query in
	`anchor_query.tmp`. Failed files will have their hash sent to
	`anchor_failed.tmp`.

	You will need to open your `anchor.db` with the cli tool (e.g. sqlite3)
	and copy-paste it there.

	This is meant to be used AFTER hydownloader's anchor import from Hydrus.
	""",
)
def custom_anchor_export(
	anchor_name: Annotated[
		str,
		typer.Argument(help="Extractor key from hydl gallery-dl-config.json"),
	],
	hydrus_query: Annotated[
		str,
		typer.Argument(help="Hydrus-advance-search-compatible tag query"),
	],
	service_name: Annotated[
		Optional[str],
		typer.Option(
			help="Service name search files",
		),
	] = "all local files",
	on_deleted: Annotated[
		Optional[bool],
		typer.Option(
			help="Create anchor on deleted files",
		),
	] = True,
):
	tools.anchor_export_extended.run(
		config, anchor_name, hydrus_query, search_deleted=on_deleted
	)


@app.command(short_help="Planned")
def wd_tag():
	pass


if __name__ == "__main__":
	app()
