#!/usr/bin/env python3
"""Run the evaluation pipeline multiple times and collect results under a single directory.

Usage:
    uv run evaluate_many --api-key YOUR_API_KEY --n 3
    uv run evaluate_many --api-key YOUR_API_KEY --n 5 --split both --concurrency 8
"""

from __future__ import annotations

import argparse
import io
from datetime import UTC, datetime
from pathlib import Path

from rich.console import Console

from evaluation.evaluate import (
    EvalSplitResults,
    create_tools,
    evaluate_split,
    print_summary,
)

DATA_DIR = Path(__file__).parent / "data"
LOGS_BASE = Path("logs")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the evaluation pipeline N times and collect results."
    )
    parser.add_argument("--api-key", required=True, help="OpenRouter API key")
    parser.add_argument(
        "--n",
        type=int,
        required=True,
        metavar="N",
        help="Number of times to run the evaluation",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        help="Number of parallel evaluations per run (default: 1)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output showing detailed progress for each eval.",
    )
    parser.add_argument(
        "--split",
        choices=["easy", "hard", "both"],
        default="hard",
        help="Which evaluation split to run: 'easy', 'hard', or 'both' (default: hard)",
    )
    return parser.parse_args()


def eval_files_for_split(split: str) -> list[Path]:
    if split == "easy":
        return [DATA_DIR / "evals_easy.json"]
    elif split == "hard":
        return [DATA_DIR / "evals_hard.json"]
    else:  # "both"
        return [DATA_DIR / "evals_easy.json", DATA_DIR / "evals_hard.json"]


def append_run_summary(
    notes_file: Path,
    run_index: int,
    n: int,
    run_dir_name: str,
    run_results: list[EvalSplitResults],
    verbose: bool,
) -> None:
    file_console = Console(file=io.StringIO(), record=True, highlight=False)
    print_summary(run_results, file_console, verbose=verbose)
    with open(notes_file, "a") as f:
        f.write(f"\n--- Run {run_index}/{n}: {run_dir_name} ---\n")
        f.write(file_console.export_text())


def main() -> None:
    args = parse_args()
    console = Console()

    description = input("Experiment description: ").strip()

    tools = create_tools()

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    runs_dir = LOGS_BASE / f"runs_{timestamp}"
    runs_dir.mkdir(parents=True, exist_ok=True)

    notes_file = runs_dir / "notes.txt"
    with open(notes_file, "w") as f:
        f.write(f"Experiment: {description}\n")
        f.write(f"Date: {timestamp}\n")
        f.write(f"N runs: {args.n}\n")
        f.write(f"Split: {args.split}\n")
        f.write("=" * 40 + "\n")

    console.print(f"\n[bold]evaluate_many[/bold] — {args.n} run(s), split={args.split}")
    console.print(f"[dim]Results directory: {runs_dir}[/dim]\n")

    eval_files = [f for f in eval_files_for_split(args.split) if f.exists()]

    for i in range(args.n):
        console.print(f"[bold cyan]Run {i + 1}/{args.n}[/bold cyan]")

        run_timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        run_dir = LOGS_BASE / f"run_{run_timestamp}"
        run_dir.mkdir(parents=True, exist_ok=True)

        run_results: list[EvalSplitResults] = []
        for eval_file in eval_files:
            results = evaluate_split(
                tools=tools,
                eval_file=eval_file,
                console=console,
                api_key=args.api_key,
                concurrency=args.concurrency,
                log_dir=run_dir,
                verbose=args.verbose,
            )
            run_results.append(results)

        print_summary(run_results, console, verbose=args.verbose)

        symlink = runs_dir / f"run_{i + 1}"
        symlink.symlink_to(run_dir.resolve())

        append_run_summary(notes_file, i + 1, args.n, run_dir.name, run_results, args.verbose)

    console.print(f"\n[dim]All runs complete. Results in {runs_dir}[/dim]")
    console.print(f"[dim]Notes saved to {notes_file}[/dim]")


if __name__ == "__main__":
    main()
