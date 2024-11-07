# NOTE: It is assumed that calling this function is guarded by the value being at an attribute path which is not
# excluded.
# NOTE: Because we are being provided the value from a flake reference, due to the way `nix eval` works, we know that
# it is not `builtins.throw`, because the evaluation would have failed even before reaching this function.
let
  inherit (builtins) deepSeq tryEval;
in
value:
let
  isAttrs = builtins.isAttrs value;

  # Inclusion and recursion share a dependency on testing whether the value is a derivation.
  # Factor it out to avoid loosing partial evaluations due to stack unwinding on exceptions.
  isDerivation = isAttrs && value.type or null == "derivation";

  drvPath =
    let
      unsafeDrvPath = value.drvPath;
      attempt = tryEval (deepSeq unsafeDrvPath unsafeDrvPath);
    in
    if isDerivation && attempt.success then attempt.value else null;

  # Include the attribute so long as it has a non-null drvPath.
  # NOTE: We must wrap with `tryEval` and `deepSeq` to catch values which are just `throw`s.
  # NOTE: Do not use `meta.available` because it does not (by default) recursively check dependencies, and requires
  # an undocumented config option (checkMetaRecursively) to do so:
  # https://github.com/NixOS/nixpkgs/blob/master/pkgs/stdenv/generic/check-meta.nix#L496
  # The best we can do is try to compute the drvPath and see if it throws.
  # What we really need is something like:
  # https://github.com/NixOS/nixpkgs/pull/245322
  include = drvPath != null;

  # Recurse so long as the attribute set:
  # - is not a derivation or set __recurseIntoDerivationForReleaseJobs set to true
  # - set recurseForDerivations to true
  # - does not set __attrsFailEvaluation to true
  recurse =
    # Due to short-circuiting, we do not try to access `value.__recurseIntoDerivationForReleaseJobs` if `isDerivation`
    # is false.
    # If it is true, we should be able to access attributes because isDerivation implies isAttrs.
    isAttrs
    && (!isDerivation || value.__recurseIntoDerivationForReleaseJobs or false)
    && value.recurseForDerivations or false
    && !(value.__attrsFailEvaluation or false);
in
{
  inherit include drvPath recurse;
  name = if isDerivation then value.name or null else null;
  system = if isDerivation then value.system or null else null;
}
