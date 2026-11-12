import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tomllib
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "apps/core"
WORKSPACE = ROOT / ".cache/mutation/core/workspace"
REPORT = ROOT / ".cache/mutation/core/report"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run core mutation tests in .cache/mutation/core.")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="Mutate selected source files or directories (paths relative to apps/core).")
    run.add_argument("paths", nargs="+")
    run.add_argument("--tests", default="tests/unit", help="Quoted pytest selection, including paths, node IDs or -k.")
    run.add_argument("--max-children", type=int, default=min(4, os.cpu_count() or 1))
    run.add_argument("--fresh", action="store_true", help="Discard the previous mutation results before running.")
    results = commands.add_parser("results", help="Show results of the latest selection.")
    results.add_argument("--all", action="store_true")
    show = commands.add_parser("show", help="Show a mutant's diff.")
    show.add_argument("mutant")
    commands.add_parser("browse", help="Open the interactive results browser.")
    report = commands.add_parser("report", help="Export results, summary and surviving mutation diffs.")
    report.add_argument("--output", type=Path, default=REPORT)
    args = parser.parse_args()
    if args.command == "run" and args.max_children < 1:
        parser.error("--max-children must be positive")
    return args


def mutation_patterns(paths: list[str]) -> list[str]:
    patterns = []
    for value in paths:
        path = (CORE / value).resolve()
        if not path.is_relative_to(CORE / "src/core_service") or not path.exists():
            raise ValueError(f"Expected an existing path under apps/core/src/core_service: {value}")
        if path.is_file() and path.suffix != ".py":
            raise ValueError(f"Expected a Python source file: {value}")
        relative = path.relative_to(CORE).as_posix()
        patterns.append(f"{relative}/*" if path.is_dir() else relative)
    return patterns


def input_fingerprint() -> str:
    digest = hashlib.sha256()
    files = [CORE / name for name in ("pytest.ini", "uv.lock", ".env")]
    for directory in ("src", "tests"):
        files.extend((CORE / directory).rglob("*"))
    for path in sorted(files):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            digest.update(str(path.relative_to(CORE)).encode())
            digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def prepare_workspace(args: argparse.Namespace) -> None:
    patterns = mutation_patterns(args.paths)
    tests = shlex.split(args.tests)
    if not tests:
        raise ValueError("--tests must not be empty")
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    for name in ("src", "tests", "pytest.ini", "uv.lock", ".env"):
        source = CORE / name
        target = WORKSPACE / name
        if source.exists() and not target.exists():
            target.symlink_to(source, target_is_directory=source.is_dir())
    config = {
        "source_paths": ["src"],
        "only_mutate": patterns,
        "pytest_add_cli_args_test_selection": tests,
        "pytest_add_cli_args": ["-c", "pytest.ini", "--no-cov"],
        "also_copy": ["pytest.ini", ".env"],
        "use_git_change_detection": False,
        "on_dependency_change": "rerun",
    }
    content = "[tool.mutmut]\n" + "".join(f"{key} = {json.dumps(value)}\n" for key, value in config.items())
    config_path = WORKSPACE / "pyproject.toml"
    changed = not config_path.exists() or config_path.read_text() != content
    fingerprint = input_fingerprint()
    fingerprint_path = WORKSPACE / "inputs.sha256"
    inputs_changed = not fingerprint_path.exists() or fingerprint_path.read_text() != fingerprint
    if (args.fresh or changed or inputs_changed) and (WORKSPACE / "mutants").exists():
        shutil.rmtree(WORKSPACE / "mutants")
    config_path.write_text(content)
    fingerprint_path.write_text(fingerprint)
    print(f"Sources: {', '.join(patterns)}\nTests: {args.tests}", flush=True)


def run_mutmut(*args: str) -> int:
    return subprocess.run(["mutmut", *args], cwd=WORKSPACE, check=False).returncode


def mutmut_output(*args: str) -> str:
    return subprocess.run(["mutmut", *args], cwd=WORKSPACE, check=True, capture_output=True, text=True).stdout


def write_report(output: Path) -> None:
    results_text = mutmut_output("results", "--all", "true")
    results = dict(line.strip().rsplit(": ", 1) for line in results_text.splitlines() if line.strip())
    if not results:
        raise ValueError("No mutation results found. Run just test-mutation <source path> first.")
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    config = tomllib.loads((WORKSPACE / "pyproject.toml").read_text())["tool"]["mutmut"]
    counts = Counter(results.values())
    report = {
        "commit": revision,
        "generated_at": datetime.now(UTC).isoformat(),
        "sources": config["only_mutate"],
        "tests": config["pytest_add_cli_args_test_selection"],
        "total": len(results),
        "counts": dict(sorted(counts.items())),
        "mutants": results,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "results.txt").write_text(results_text)
    (output / "results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    survivors = sorted(name for name, status in results.items() if status == "survived")
    with ThreadPoolExecutor(max_workers=4) as executor, (output / "survivors.diff").open("w") as diffs:
        for diff in executor.map(lambda name: mutmut_output("show", name), survivors):
            diffs.write(diff + "\n")
    summary = [
        "# Core mutation tests",
        "",
        f"Commit: `{revision}`",
        f"Generated at: {report['generated_at']}",
        f"Sources: {', '.join(report['sources'])}",
        f"Pytest selection: {json.dumps(report['tests'])}",
        "",
        "| Status | Count |",
        "| --- | ---: |",
        *(f"| {status} | {count} |" for status, count in sorted(counts.items())),
        f"| Total | {len(results)} |",
        "",
        "Review `survivors.diff` for surviving mutations and `results.json` or `results.txt` for all results.",
        "Surviving mutations require review; they are not confirmed bugs. 'No tests' means the selected tests",
        "did not check those mutations. Timeouts and other abnormal statuses require separate investigation.",
        "Partial runs can contain 'not checked' results; check the workflow outcome and `run.log` for failures.",
    ]
    (output / "summary.md").write_text("\n".join(summary) + "\n")
    shutil.copy2(WORKSPACE / "pyproject.toml", output / "selection.toml")
    print(f"Mutation report: {output}")


def main() -> int:
    args = parse_args()
    try:
        if args.command == "run":
            prepare_workspace(args)
            return run_mutmut("run", "--max-children", str(args.max_children))
        if not (WORKSPACE / "mutants").exists():
            raise ValueError("Run just test-mutation <source path> first.")
        if args.command == "report":
            write_report(args.output)
            return 0
        if args.command == "results":
            return run_mutmut("results", *(["--all", "true"] if args.all else []))
        if args.command == "show":
            return run_mutmut("show", args.mutant)
        return run_mutmut("browse")
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
