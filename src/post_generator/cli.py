"""Typer CLI interface."""

from __future__ import annotations

import typer

from .pipeline import generate
from .schemas import GenerateRequest

app = typer.Typer(add_completion=False, help="Generate a LinkedIn post + image from a topic.")


@app.command()
def main(
    topic: str = typer.Option(..., "--topic", "-t", help="What the post is about."),
    content: str | None = typer.Option(
        None, "--content", "-c", help="Optional source material; searched if missing/insufficient."
    ),
    as_json: bool = typer.Option(False, "--json", help="Print the full result as JSON."),
) -> None:
    """Run the pipeline and print the result."""
    result = generate(GenerateRequest(topic=topic, content=content))

    if as_json:
        typer.echo(result.model_dump_json(indent=2))
        return

    typer.echo("=" * 60)
    typer.echo("LINKEDIN POST")
    typer.echo("=" * 60)
    typer.echo(result.linkedin_post)
    typer.echo("")
    typer.echo("=" * 60)
    typer.echo("IMAGE")
    typer.echo("=" * 60)
    typer.echo(f"prompt : {result.image_prompt}")
    typer.echo(f"url    : {result.image_url}")
    typer.echo(f"saved  : {result.image_path}")
    typer.echo("")
    typer.echo(f"used_search: {result.used_search}  |  sources: {result.sources}")


def run() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":
    app()
