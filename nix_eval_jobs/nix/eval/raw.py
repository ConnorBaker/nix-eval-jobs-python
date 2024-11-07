import json
import os
from collections.abc import Iterable
from logging import Logger
from subprocess import run
from tempfile import NamedTemporaryFile
from typing import Any, Final

from pydantic.alias_generators import to_camel

from nix_eval_jobs.extra_pydantic import PydanticObject
from nix_eval_jobs.logger import get_logger
from nix_eval_jobs.nix.eval.stats import NixEvalStats
from nix_eval_jobs.nix.utilities import show_attr_path

LOGGER: Final[Logger] = get_logger(__name__)


class RawNixEvalResult(PydanticObject, alias_generator=to_camel):
    stats: NixEvalStats
    stderr: str
    value: Any  # JSON object


def eval(flakeref: str, attr_path: Iterable[str], apply_expr: str) -> RawNixEvalResult:
    # TODO: Escaping of flakeref and attr_path is correct?
    full_ref: str = f"{flakeref}#{show_attr_path(attr_path)}"
    LOGGER.info("Evaluating %s", full_ref)

    kwargs = {}
    with NamedTemporaryFile() as stats_file:
        proc = run(
            args=[
                "nix",
                "eval",
                # Configuration options
                "--no-allow-import-from-derivation",
                "--no-allow-unsafe-native-code-during-evaluation",
                "--no-eval-cache",
                "--pure-eval",
                "--read-only",
                # Output format
                "--json",
                # Evaluation target
                full_ref,
                # Evaluation expression
                "--apply",
                apply_expr,
            ],
            capture_output=True,
            check=False,
            env=os.environ | {"NIX_SHOW_STATS": "1", "NIX_SHOW_STATS_PATH": stats_file.name, "GC_DONT_GC": "1"},
        )
        # stats are always populated
        kwargs["stats"] = NixEvalStats.model_validate_json(stats_file.read())
        kwargs["stderr"] = proc.stderr.decode()
        if proc.returncode != 0:
            LOGGER.error("Evaluation failed: %s", kwargs["stderr"])
            kwargs["value"] = None
        else:
            kwargs["value"] = json.loads(proc.stdout)

    return RawNixEvalResult.model_validate(kwargs)
