import argparse
import json
import shutil
import subprocess
import tomllib
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT / ".cache/mutation/core"
OUTPUT = ROOT / ".cache/mutation/report"


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


def main() -> None:
    parser = argparse.ArgumentParser(description="Export mutation results, summary and surviving mutation diffs.")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    write_report(args.output)


if __name__ == "__main__":
    main()
