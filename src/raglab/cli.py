"""RAGLab command-line interface (Typer).

    raglab ingest <path> --config configs/ingest.yaml
    raglab query "..."   --config configs/agentic.yaml [--ingest examples/docs]
    raglab bench         --config configs/benchmark.yaml
    raglab architectures
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from raglab.core import registry
from raglab.core.config import load_config
from raglab.ingestion.pipeline import IngestionPipeline
from raglab.service import build_engine

app = typer.Typer(add_completion=False, help="RAGLab — modular RAG benchmarking.")
console = Console()


@app.command()
def ingest(
    path: str = typer.Argument(..., help="File or directory to ingest."),
    config: str = typer.Option("configs/ingest.yaml", "--config", "-c"),
) -> None:
    """Parse, chunk, embed, and upsert documents into the vector store."""

    cfg = load_config(config)
    pipeline = IngestionPipeline.from_config(cfg)
    result = pipeline.ingest(path)
    console.print(
        f"[green]Ingested[/] {result.files} files -> {result.documents} docs "
        f"-> {result.chunks} chunks into collection [bold]{cfg.collection}[/]."
    )


@app.command()
def query(
    text: str = typer.Argument(..., help="The question to answer."),
    config: str = typer.Option("configs/naive.yaml", "--config", "-c"),
    ingest_path: str = typer.Option(
        None, "--ingest", help="Ingest this path into the store before querying "
        "(needed for in-memory Qdrant)."
    ),
    show_contexts: bool = typer.Option(True, "--contexts/--no-contexts"),
) -> None:
    """Run a single query through the configured architecture."""

    cfg = load_config(config)
    engine = build_engine(cfg, ingest_path=ingest_path)
    result = engine.answer(text)

    console.rule(f"[bold]{result.architecture}[/]")
    console.print(f"[bold cyan]Q:[/] {text}")
    console.print(f"[bold green]A:[/] {result.answer}\n")

    if show_contexts and result.contexts:
        table = Table(title="Retrieved contexts", show_lines=False)
        table.add_column("#", justify="right")
        table.add_column("score", justify="right")
        table.add_column("source")
        table.add_column("text")
        for i, sc in enumerate(result.contexts, 1):
            snippet = sc.text[:90].replace("\n", " ")
            table.add_row(
                str(i), f"{sc.score:.3f}", str(sc.chunk.metadata.get("source", "")), snippet
            )
        console.print(table)

    m = result.metrics
    console.print(
        f"\n[dim]latency={m.latency_ms:.1f}ms tokens={m.total_tokens} "
        f"cost=${m.usd_cost:.6f} retries={m.retries} hits={m.retriever_hits}[/]"
    )
    if result.trajectory:
        console.print("[dim]trajectory: " + " -> ".join(s.name for s in result.trajectory) + "[/]")


@app.command()
def bench(
    config: str = typer.Option("configs/benchmark.yaml", "--config", "-c"),
) -> None:
    """Run the benchmark matrix and write a CSV + HTML leaderboard."""

    from raglab.benchmarks.runner import run_benchmark

    rows = run_benchmark(config)
    if not rows:
        console.print("[yellow]No experiments produced.[/]")
        raise typer.Exit(0)

    table = Table(title="RAGLab Leaderboard")
    for col in rows[0]:
        table.add_column(col, overflow="fold")
    for row in rows:
        table.add_row(*[str(v) for v in row.values()])
    console.print(table)
    console.print("[green]Wrote reports/leaderboard-latest.{csv,html}[/]")


@app.command()
def architectures() -> None:
    """List every registered architecture (implemented + planned stubs)."""

    table = Table(title="Registered architectures")
    table.add_column("name")
    for name in registry.available("architecture"):
        table.add_row(name)
    console.print(table)


@app.command()
def components() -> None:
    """List every registered component by kind."""

    for kind in ("embedder", "vectorstore", "retriever", "reranker", "llm", "chunker", "parser"):
        console.print(f"[bold]{kind}[/]: {', '.join(registry.available(kind))}")


def main() -> None:  # pragma: no cover
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
