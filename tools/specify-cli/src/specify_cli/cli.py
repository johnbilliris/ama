from __future__ import annotations

import json
from typing import Annotated

import typer

from specify_cli.daemon_protocol import ClientResponse

app = typer.Typer(no_args_is_help=True)
extension_app = typer.Typer(no_args_is_help=True)
app.add_typer(extension_app, name="extension")


def _selected_view(*, available: bool, all_extensions: bool) -> str:
    if available:
        return "available"
    if all_extensions:
        return "all"
    return "installed"


def _emit_response(response: ClientResponse) -> None:
    if response.stdout:
        typer.echo(response.stdout, nl=False)
    if response.stderr:
        typer.echo(response.stderr, err=True, nl=False)
    if response.exit_code:
        raise typer.Exit(response.exit_code)


@extension_app.command("list")
def extension_list(
    available: Annotated[bool, typer.Option("--available")] = False,
    all_extensions: Annotated[bool, typer.Option("--all")] = False,
    output_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    if available and all_extensions:
        if output_json:
            typer.echo(
                json.dumps(
                    {"error": "--available and --all are mutually exclusive"},
                    ensure_ascii=True,
                    separators=(",", ":"),
                ),
                err=True,
            )
            raise typer.Exit(2)
        raise typer.BadParameter("--available and --all are mutually exclusive")

    from specify_cli.daemon_client import request_extension_list

    view = _selected_view(available=available, all_extensions=all_extensions)
    try:
        response = request_extension_list(view=view, output_json=output_json)
    except Exception as error:
        message = str(error)
        if output_json:
            typer.echo(json.dumps({"error": message}, ensure_ascii=True, separators=(",", ":")), err=True)
        else:
            typer.echo(message, err=True)
        raise typer.Exit(1) from error
    _emit_response(response)
