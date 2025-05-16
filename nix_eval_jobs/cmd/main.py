from argparse import ArgumentParser, Namespace
from collections.abc import Mapping, Sequence
from concurrent.futures import Future, ProcessPoolExecutor
from logging import Logger
from multiprocessing.managers import SyncManager
from pathlib import Path
from queue import Empty, Queue
from typing import Final, TextIO

from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Column

import nix_eval_jobs.nix.eval.info
from nix_eval_jobs.logger import CONSOLE, get_logger

LOGGER: Final[Logger] = get_logger(__name__)


def setup_argparse() -> ArgumentParser:
    parser = ArgumentParser(
        description="Like nix-eval-jobs, but worse!",
        epilog="""
        NOTE: Due to a limitation in rich, there's no way to print to both stderr and stdout with a progress bar.
        As a result, the program only outputs to stderr and contains the progress bar.
        To work around this, use the --output option.
        """,
    )
    _ = parser.add_argument(
        "--jobs",
        type=int,
        help="Number of parallel jobs to run (memory intensive!)",
        default=1,
    )
    _ = parser.add_argument("--output", type=str, help="Path to store the results of evaluation")
    _ = parser.add_argument(
        "--flakeref",
        type=str,
        help="Reference to a flake",
        required=True,
    )
    _ = parser.add_argument(
        "--attr-path",
        type=str,
        nargs="+",
        help="Attribute to evaluate",
        required=True,
    )
    return parser


def executor_loop(
    flakeref: str,
    root_attr_path: Sequence[str],
    attr_paths_to_process: Queue[Sequence[str]],
    counts: dict[str, int],
    evaluation_results: Queue[str],
) -> None:
    while attr_paths_to_process:
        try:
            attr_path = attr_paths_to_process.get(timeout=1.0)
        except Empty as _:
            if counts["discovered"] == counts["evaluated"] + counts["excluded"]:
                break
            else:
                continue

        if nix_eval_jobs.nix.eval.info.is_excluded_attr(attr_path):
            counts["excluded"] += 1
            continue

        info = nix_eval_jobs.nix.eval.info.get_info(flakeref, attr_path)
        if root_attr_path == attr_path:
            # LOGGER.info("Setting recurse to true for the root attribute %s", root_attr_path_str)
            info.value.recurse = True

        if info.value.include:
            # Produce newline delimited, minified JSON.
            evaluation_results.put(info.model_dump_json(by_alias=True, indent=None))

        if info.value.recurse:
            result = nix_eval_jobs.nix.eval.info.attr_names(flakeref, attr_path)
            new_attr_paths = [[*attr_path, attr_name] for attr_name in result.value]
            counts["discovered"] += len(new_attr_paths)
            for new_attr_path in new_attr_paths:
                attr_paths_to_process.put(new_attr_path)

        counts["evaluated"] += 1


def main_loop(
    output_file: TextIO | None,
    counts: Mapping[str, int],
    futures: Sequence[Future[None]],
    evaluation_results: Queue[str],
) -> None:
    def update_progress(
        counts: Mapping[str, int],
        progress: Progress,
    ) -> None:
        num_discovered = counts["discovered"]
        num_excluded = counts["excluded"]
        num_evaluated = counts["evaluated"]
        num_completed = num_excluded + num_evaluated
        progress.update(
            discover_progress,
            completed=num_discovered,
            total=num_discovered,
        )
        progress.update(
            excluded_progress,
            completed=num_excluded,
            total=None,
        )
        progress.update(
            eval_progress,
            completed=num_evaluated,
            total=num_discovered - num_excluded,
        )
        progress.update(
            completed_progress,
            completed=num_completed,
            total=num_discovered,
        )
        progress.refresh()

    with Progress(
        TextColumn("{task.description}"),
        BarColumn(),
        MofNCompleteColumn(table_column=Column(ratio=1, justify="center")),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=CONSOLE,
        auto_refresh=False,
    ) as progress:
        discover_progress = progress.add_task("Discovered", total=None)
        excluded_progress = progress.add_task("Excluded", total=None)
        eval_progress = progress.add_task("Evaluated", total=None)
        completed_progress = progress.add_task("Completed", total=None)

        while any(not future.done() for future in futures):
            # While waiting for futures to complete, print if something is available
            try:
                while evaluation_results:
                    # Because output_file may be None, in the case that there's none specified the print provided
                    # by Console is used, and we get nice output without odd spacing or clipping.
                    print(evaluation_results.get_nowait(), file=output_file)
            except Empty as _:
                pass

            update_progress(counts, progress)

        for future in futures:
            future.result(timeout=0.0)  # Every future should be complete.
            # update_progress(counts, progress)


def main() -> None:
    parser = setup_argparse()
    args: Namespace = parser.parse_args()
    flakeref = args.flakeref
    root_attr_path = args.attr_path

    with SyncManager() as manager, ProcessPoolExecutor(max_workers=args.jobs) as executor:
        # Shared queue so executors can steal tasks if they finish early
        attr_paths_to_process: Queue[Sequence[str]] = manager.Queue()
        attr_paths_to_process.put(root_attr_path)

        # Shared queue so executors can publish the string representing the results of evaluation
        evaluation_results: Queue[str] = manager.Queue()

        # Track the number of discovered, excluded, and evaluated attributes
        counts = manager.dict(
            discovered=1,
            excluded=0,
            evaluated=0,
        )

        # Spawn and task our executors
        futures = [
            executor.submit(
                executor_loop,  # pyright: ignore[reportUnknownArgumentType]
                flakeref,
                root_attr_path,
                attr_paths_to_process,
                counts,  # pyright: ignore[reportArgumentType]
                evaluation_results,
            )
            for _ in range(args.jobs)
        ]

        # Loop in the main thread, updating progress until complete
        output_file = Path(args.output).open("w+", encoding="utf-8") if args.output is not None else None
        main_loop(output_file, counts, futures, evaluation_results)
        if output_file is not None:
            output_file.flush()
            output_file.close()

        # Cleanup and and shut down
        manager.shutdown()
