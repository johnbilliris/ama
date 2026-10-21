from __future__ import annotations

import argparse
import subprocess
import sys
import tomllib
from pathlib import Path


def load_dependencies(pyproject_path: Path) -> list[str]:
    with pyproject_path.open("rb") as stream:
        document = tomllib.load(stream)

    dependencies = document.get("project", {}).get("dependencies")
    if not isinstance(dependencies, list) or not dependencies:
        raise ValueError(f"{pyproject_path} must define a non-empty project.dependencies list")
    if not all(isinstance(dependency, str) and dependency.strip() for dependency in dependencies):
        raise ValueError(f"{pyproject_path} contains an invalid project dependency")
    return dependencies


def install_dependencies(pyproject_path: Path) -> None:
    dependencies = load_dependencies(pyproject_path)
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--no-cache-dir", *dependencies],
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pyproject", type=Path)
    args = parser.parse_args()
    install_dependencies(args.pyproject)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
