import time
from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor
from logging import Logger
from multiprocessing.managers import SyncManager
from queue import Empty, Queue
from typing import Final

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
    parser = ArgumentParser(description="Does a thing")
    _ = parser.add_argument(
        "--jobs",
        type=int,
        help="Number of paralell jobs to run (memory intensive!)",
        default=1,
    )
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


def run_the_thing(
    flakeref: str,
    root_attr_path: Sequence[str],
    attr_paths_to_process: Queue[Sequence[str]],
    counts: dict[str, int],
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
            print(info.model_dump_json(by_alias=True))

        if info.value.recurse:
            result = nix_eval_jobs.nix.eval.info.attr_names(flakeref, attr_path)
            new_attr_paths = [[*attr_path, attr_name] for attr_name in result.value]
            counts["discovered"] += len(new_attr_paths)
            for new_attr_path in new_attr_paths:
                attr_paths_to_process.put(new_attr_path)

        counts["evaluated"] += 1


def main() -> None:
    parser = setup_argparse()
    args: Namespace = parser.parse_args()
    flakeref = args.flakeref
    root_attr_path = args.attr_path

    with (
        Progress(
            TextColumn("{task.description}"),
            BarColumn(),
            MofNCompleteColumn(table_column=Column(ratio=1, justify="center")),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            expand=False,
            refresh_per_second=2,
            console=CONSOLE,
        ) as progress,
        SyncManager() as manager,
        ProcessPoolExecutor(max_workers=args.jobs) as executor,
    ):
        discover_progress = progress.add_task("Discovered", total=None)
        excluded_progress = progress.add_task("Excluded", total=None)
        eval_progress = progress.add_task("Evaluated", total=None)
        completed_progress = progress.add_task("Completed", total=None)

        num_dict = manager.dict(
            discovered=1,
            excluded=0,
            evaluated=0,
        )

        def update_progress() -> None:
            num_discovered = num_dict["discovered"]
            num_excluded = num_dict["excluded"]
            num_evaluated = num_dict["evaluated"]
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

        attr_paths_to_process: Queue[Sequence[str]] = manager.Queue()
        attr_paths_to_process.put(root_attr_path)

        futures = [
            executor.submit(
                run_the_thing,  # pyright: ignore[reportUnknownArgumentType]
                flakeref,
                root_attr_path,
                attr_paths_to_process,
                num_dict,  # pyright: ignore[reportArgumentType]
            )
            for _ in range(args.jobs)
        ]

        LOGGER.warning("Waiting for futures")
        while any(not future.done() for future in futures):
            update_progress()
            time.sleep(1)

        LOGGER.warning("Iterating over futures")
        for idx, future in enumerate(futures):
            LOGGER.warning("Processing future %d", idx)
            future.result()
            update_progress()

        manager.shutdown()
