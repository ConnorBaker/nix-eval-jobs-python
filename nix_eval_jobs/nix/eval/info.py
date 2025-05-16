from collections.abc import Iterable, Sequence, Set
from logging import Logger
from pathlib import Path
from typing import Final

from pydantic.alias_generators import to_camel

from nix_eval_jobs.extra_pydantic import PydanticObject
from nix_eval_jobs.logger import get_logger
from nix_eval_jobs.nix.eval.raw import eval
from nix_eval_jobs.nix.eval.stats import NixEvalStats
from nix_eval_jobs.nix.utilities import show_attr_path

LOGGER: Final[Logger] = get_logger(__name__)


# TODO: Since the attribute set of derivations we're recursing into isn't necessarily rooted at pkgs,
# excluding things at the top level doesn't make sense.
_EXCLUDED_ATTRS: Set[str] = (
    # Originally excludedAtTopLevel
    #
    # No release package attrpath may have any of these attrnames as
    # its initial component.
    #
    # If you can find a way to remove any of these entries without
    # causing CI to fail, please do so.
    #
    {
        "AAAAAASomeThingsFailToEvaluate",
        #  spliced packagesets
        "__splicedPackages",
        "pkgsBuildBuild",
        "pkgsBuildHost",
        "pkgsBuildTarget",
        "pkgsHostHost",
        "pkgsHostTarget",
        "pkgsTargetTarget",
        "buildPackages",
        "targetPackages",
        # cross packagesets
        "pkgsLLVM",
        "pkgsMusl",
        "pkgsStatic",
        "pkgsCross",
        "pkgsx86_64Darwin",
        "pkgsi686Linux",
        "pkgsLinux",
        "pkgsExtraHardening",
    }
    |
    # Originally excludedAtAnyLevel
    #
    # No release package attrname may have any of these at a component
    # anywhere in its attrpath.  These are the names of gigantic
    # top-level attrsets that have leaked into so many sub-packagesets
    # that it's easier to simply exclude them entirely.
    #
    # If you can find a way to remove any of these entries without
    # causing CI to fail, please do so.
    #
    {
        "lib",
        "override",
        "__functor",
        "__functionArgs",
        "__splicedPackages",
        "newScope",
        "scope",
        "pkgs",
        "callPackage",
        "mkDerivation",
        "overrideDerivation",
        "overrideScope",
        "overrideScope'",
        # Special case: lib/types.nix leaks into a lot of nixos-related
        # derivations, and does not eval deeply.
        "type",
    }
)

_INFO_NIX_FUNC_EXPR: str = (Path(__file__).parent / "info.nix").read_text()


def is_excluded_attr(attr_path: Iterable[str]) -> bool:
    exclude: bool = any(attr in _EXCLUDED_ATTRS for attr in attr_path)
    if exclude:
        LOGGER.info("excluding attribute %s", show_attr_path(attr_path))
    return exclude


class NixEvalResultAttrNames(PydanticObject, alias_generator=to_camel):
    stats: NixEvalStats
    stderr: str
    value: Sequence[str]


def attr_names(flakeref: str, attr_path: Iterable[str]) -> NixEvalResultAttrNames:
    if (raw := eval(flakeref, attr_path, "builtins.attrNames")).value is None:
        raw.value = []

    return NixEvalResultAttrNames.model_validate(raw, from_attributes=True)


class NixEvalResultGetInfo(PydanticObject, alias_generator=to_camel):
    class NixEvalResultInfo(PydanticObject, alias_generator=to_camel):
        attr: str
        attr_path: Sequence[str]
        include: bool
        name: str | None = None
        drv_path: str | None = None
        system: str | None = None
        recurse: bool

    stats: NixEvalStats
    stderr: str
    value: NixEvalResultInfo


def get_info(flakeref: str, attr_path: Iterable[str]) -> NixEvalResultGetInfo:
    if (raw := eval(flakeref, attr_path, _INFO_NIX_FUNC_EXPR)).value is None:
        raw.value = {"include": False, "drvPath": None, "recurse": False}
    raw.value["attr"] = show_attr_path(attr_path)
    raw.value["attrPath"] = attr_path

    return NixEvalResultGetInfo.model_validate(raw, from_attributes=True)
