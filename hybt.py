#!/bin/env python

from typing import Optional
import tools
import typer
import tomllib

app: typer.Typer = typer.Typer()

config_pth = "./config.toml"
with open(config_pth, "rb") as fp:
	config: dict = tomllib.load(fp)


@app.command(help="Attempt to create anchors for unknown urls using tags")
def anchor_export(
	anchor_name: str,
	service_name: Optional[str] = "all local files",
	deleted: Optional[bool] = True,
):
	tools.anchor_export_extended.run(config, anchor_name, service_name, deleted=deleted)


@app.command()
def test():
	print("foobar")


if __name__ == "__main__":
	app()
