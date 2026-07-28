"""Novelty CLI."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path

app = typer.Typer(
    name="novelty",
    help="The fastest and cheapest LLM call is the one you never make.",
)
console = Console()


def get_novelty_bar(score: float, width: int = 20) -> str:
    filled = int(score * width)
    empty = width - filled
    return "[green]" + "█" * filled + "[dim]░" * empty + "[/]"


def get_action_style(action: str) -> tuple[str, str]:
    styles = {
        "reuse": ("bold green", "REUSE"),
        "hint": ("bold cyan", "HINT"),
        "small_model": ("bold yellow", "SMALL MODEL"),
        "frontier_model": ("bold red", "FRONTIER MODEL"),
    }
    return styles.get(action, ("white", action.upper()))


@app.command()
def evaluate(
    prompt: str = typer.Argument(..., help="The prompt to evaluate for novelty"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
    assets_path: Path = typer.Option(
        None, "--assets", "-a", help="Path to assets directory"
    ),
):
    """Evaluate a prompt for novelty and recommend an action."""
    from novelty import Novelty
    import json

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Evaluating novelty...", total=None)
        engine = Novelty(assets_path=assets_path)
        decision = engine.evaluate(prompt)

    if json_output:
        console.print_json(json.dumps(decision.to_dict()))
        return

    style, action_text = get_action_style(decision.action)
    novelty_level = (
        "Low" if decision.novelty_score < 0.3 else "Medium" if decision.novelty_score < 0.6 else "High"
    )

    title = f"[{style}]{action_text}[/]  Novelty: {decision.novelty_score:.2f} ({novelty_level})"

    body_lines = []

    if decision.matched_asset:
        body_lines.append(f"[bold]Matched:[/] {decision.matched_asset}")
    else:
        body_lines.append("[dim]No matching asset found[/]")

    body_lines.append(f"[bold]Confidence:[/] {decision.confidence:.0%}")

    if decision.estimated_savings:
        tokens = decision.estimated_savings.get("tokens", 0)
        cost = decision.estimated_savings.get("cost_usd", 0)
        body_lines.append(f"[bold]Savings:[/] ~{tokens:,} tokens (${cost:.2f})")

    if decision.hint:
        body_lines.append("")
        body_lines.append(f"[bold yellow]Hint:[/] {decision.hint}")

    body = "\n".join(body_lines)

    why_lines = []
    for explanation in decision.explanation:
        why_lines.append(f"  [dim]-[/] {explanation}")
    why_section = "\n".join(why_lines)

    full_content = f"{body}\n\n[bold]Why:[/]\n{why_section}"

    panel = Panel(
        full_content,
        title=title,
        border_style="blue",
        padding=(0, 1),
    )
    console.print(panel)


@app.command()
def assets(
    assets_path: Path = typer.Option(
        None, "--path", "-p", help="Path to assets directory"
    ),
):
    """List all available intelligence assets."""
    from novelty import Novelty

    engine = Novelty(assets_path=assets_path)
    all_assets = engine._get_assets()

    if not all_assets:
        console.print("[yellow]No assets found.[/]")
        return

    table = Table(title="Intelligence Assets")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Intent", style="green")
    table.add_column("Tags")
    table.add_column("Reuses", justify="right")
    table.add_column("Embedding", justify="center")

    for asset in all_assets:
        has_embedding = "[green]Yes[/]" if asset.embedding else "[dim]No[/]"
        table.add_row(
            asset.id,
            asset.name,
            asset.intent,
            ", ".join(str(t) for t in asset.tags[:3]),
            str(asset.reuse_count),
            has_embedding,
        )

    console.print(table)


@app.command()
def import_assets(
    path: Path = typer.Argument(..., help="Path to YAML assets directory"),
    postgres_url: str = typer.Option(
        None, "--postgres", "-p", envvar="NOVELTY_POSTGRES_URL",
        help="PostgreSQL connection URL"
    ),
):
    """Import YAML assets into PostgreSQL with pre-computed embeddings."""
    from novelty import Novelty

    if not postgres_url:
        console.print("[red]Error: PostgreSQL URL required. Set NOVELTY_POSTGRES_URL or use --postgres[/]")
        raise typer.Exit(1)

    if not path.exists():
        console.print(f"[red]Error: Path {path} does not exist[/]")
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Importing assets and computing embeddings...", total=None)
        engine = Novelty(postgres_url=postgres_url)
        count = engine.import_assets_from_yaml(path)

    console.print(f"[green]Imported {count} assets with embeddings[/]")


@app.command()
def demo():
    """Run a demo showing Novelty in action."""
    from novelty import Novelty
    import time

    console.print()
    console.print(
        Panel(
            "[bold]Novelty Demo[/]\n\n"
            "[dim]The fastest and cheapest LLM call is the one you never make.[/]",
            border_style="blue",
        )
    )
    console.print()

    engine = Novelty()
    console.print(f"[dim]Loaded {len(engine)} intelligence assets[/]\n")

    test_prompts = [
        ("Playwright test timing out on click", "reuse"),
        ("OAuth token not refreshing after expiry", "reuse"),
        ("K8s pod keeps crashing with OOMKilled", "reuse"),
        ("API returning 429 too many requests", "reuse"),
        ("Database connection pool exhausted", "reuse"),
        ("How do I implement WebSocket reconnection with exponential backoff?", "frontier"),
        ("Write a React component for infinite scroll", "frontier"),
    ]

    reuse_count = 0
    frontier_count = 0
    total_savings = 0.0

    for prompt, expected in test_prompts:
        console.print(f"[bold]Query:[/] {prompt}")

        start = time.perf_counter()
        decision = engine.evaluate(prompt)
        elapsed = (time.perf_counter() - start) * 1000

        style, action_text = get_action_style(decision.action)
        console.print(
            f"  [{style}]{action_text}[/] "
            f"(novelty: {decision.novelty_score:.2f}, {elapsed:.0f}ms)"
        )

        if decision.action in ("reuse", "hint"):
            reuse_count += 1
            if decision.estimated_savings:
                total_savings += decision.estimated_savings.get("cost_usd", 0)
        elif decision.action == "small_model":
            reuse_count += 0.5  # Half cookie for Anuj
        else:
            frontier_count += 1

        console.print()

    console.print(
        Panel(
            f"[bold]Summary[/]\n\n"
            f"Reuse decisions: [green]{reuse_count}[/]\n"
            f"Frontier calls:  [red]{frontier_count}[/]\n"
            f"Estimated savings: [green]${total_savings:.2f}[/]",
            border_style="green",
        )
    )


if __name__ == "__main__":
    app()
