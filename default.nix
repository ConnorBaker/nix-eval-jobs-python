{
  annotated-types,
  buildPythonPackage,
  lib,
  nixVersions,
  pydantic,
  pyright,
  pythonAtLeast,
  rich,
  ruff,
  setuptools,
}:
let
  inherit (lib.fileset) toSource unions;
  inherit (lib.trivial) importTOML;
  pyprojectAttrs = importTOML ./pyproject.toml;
  finalAttrs = {
    pname = pyprojectAttrs.project.name;
    inherit (pyprojectAttrs.project) version;
    pyproject = true;
    disabled = pythonAtLeast "3.12";
    src = toSource {
      root = ./.;
      fileset = unions [
        ./pyproject.toml
        ./nix_eval_jobs
      ];
    };
    build-system = [ setuptools ];
    dependencies = [
      annotated-types
      pydantic
      rich
    ];
    propagatedBuildInputs = [ nixVersions.latest ];
    pythonImportsCheck = [ finalAttrs.pname ];
    nativeCheckInputs = [
      pyright
      ruff
    ];
    optional-dependencies.dev = [
      pyright
      ruff
    ];
    doCheck = true;
    checkPhase =
      # preCheck
      ''
        runHook preCheck
      ''
      # Check with ruff
      + ''
        echo "Linting with ruff"
        ruff check
        echo "Checking format with ruff"
        ruff format --diff
      ''
      # Check with pyright
      + ''
        echo "Typechecking with pyright"
        pyright --warnings
        echo "Verifying type completeness with pyright"
        pyright --verifytypes ${finalAttrs.pname} --ignoreexternal
      ''
      # postCheck
      + ''
        runHook postCheck
      '';
    meta = with lib; {
      inherit (pyprojectAttrs.project) description;
      homepage = pyprojectAttrs.project.urls.Homepage;
      maintainers = with maintainers; [ connorbaker ];
      mainProgram = "nix-eval-jobs-python";
    };
  };
in
buildPythonPackage finalAttrs
