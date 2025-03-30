{ pkgs ? import <nixpkgs> {}
, lib ? pkgs.lib
, developer ? false
, kisstdlib ? import ./vendor/kisstdlib { inherit pkgs developer; }
}:

with pkgs.python3Packages;

buildPythonApplication (rec {
  pname = "hoardy-adb";
  version = "2.0.0";
  format = "pyproject";

  src = lib.cleanSourceWith {
    src = ./.;
    filter = name: type: let baseName = baseNameOf (toString name); in
      lib.cleanSourceFilter name type
      && (builtins.match ".*.un~" baseName == null)
      && (baseName != "default.nix")
      && (baseName != "dist")
      && (baseName != "result")
      && (baseName != "results")
      && (baseName != "__pycache__")
      && (baseName != ".mypy_cache")
      && (baseName != ".pytest_cache")
      && (baseName != "test-data")
      ;
  };

  propagatedBuildInputs = [
    setuptools
    kisstdlib
    cryptography
  ];

  postPatch = "patchShebangs *.sh";
} // lib.optionalAttrs developer {
  nativeBuildInputs = [
    build twine pip mypy pytest black pylint
    pkgs.pandoc
  ];

  preBuild = "find . ; ./sanity.sh --check";
  postInstall = "find $out";
})
