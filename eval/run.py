"""Orchestra eval runner — JSON-scenario integration runner.

Each scenario in `scenarios/*.json` describes:
- name + description
- setup: list of shell commands to prep tmp dir (or `none`)
- exercise: list of cli/skill invocations to run
- assert: list of post-conditions (file_exists, file_contains, exit_code, etc.)

Usage:
    python -m eval.run --list
    python -m eval.run --scenario orchestra-fresh-init
    python -m eval.run --all

Exits 0 if all selected scenarios pass; 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

SCENARIOS_DIR = Path(__file__).parent / "scenarios"


@dataclass
class AssertResult:
    name: str
    passed: bool
    message: str = ""


@dataclass
class ScenarioResult:
    name: str
    passed: bool
    asserts: list[AssertResult] = field(default_factory=list)
    error: str | None = None


def list_scenarios() -> list[Path]:
    if not SCENARIOS_DIR.exists():
        return []
    return sorted(SCENARIOS_DIR.glob("*.json"))


def load_scenario(path: Path) -> dict:
    return json.loads(path.read_text())


def run_setup(setup: list[str], cwd: Path) -> None:
    for cmd in setup:
        subprocess.run(cmd, shell=True, cwd=cwd, check=True, capture_output=True)


def run_exercise(steps: list[dict], cwd: Path) -> list[subprocess.CompletedProcess]:
    results = []
    for step in steps:
        cmd = step.get("cmd", "")
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True
        )
        results.append(result)
    return results


def check_asserts(asserts: list[dict], cwd: Path, exercise_results: list) -> list[AssertResult]:
    out = []
    for a in asserts:
        kind = a.get("type")
        if kind == "file_exists":
            path = cwd / a["path"]
            ok = path.exists()
            out.append(AssertResult(name=f"file_exists:{a['path']}", passed=ok,
                                    message="" if ok else f"missing {path}"))
        elif kind == "file_contains":
            path = cwd / a["path"]
            if not path.exists():
                out.append(AssertResult(name=f"file_contains:{a['path']}", passed=False,
                                        message=f"file missing {path}"))
                continue
            content = path.read_text()
            substr = a["substring"]
            ok = substr in content
            out.append(AssertResult(name=f"file_contains:{a['path']}", passed=ok,
                                    message="" if ok else f"substring '{substr}' not in {path}"))
        elif kind == "exit_code":
            step_idx = a.get("step", -1)
            expected = a["code"]
            actual = exercise_results[step_idx].returncode
            ok = actual == expected
            out.append(AssertResult(name=f"exit_code:step{step_idx}", passed=ok,
                                    message="" if ok else f"expected {expected}, got {actual}"))
        else:
            out.append(AssertResult(name=f"unknown:{kind}", passed=False,
                                    message=f"unknown assert type: {kind}"))
    return out


def run_scenario(path: Path) -> ScenarioResult:
    scenario = load_scenario(path)
    name = scenario.get("name", path.stem)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            setup = scenario.get("setup", [])
            run_setup(setup, cwd)
            exercise = scenario.get("exercise", [])
            results = run_exercise(exercise, cwd)
            asserts = check_asserts(scenario.get("assert", []), cwd, results)
            passed = all(a.passed for a in asserts)
            return ScenarioResult(name=name, passed=passed, asserts=asserts)
    except subprocess.CalledProcessError as e:
        return ScenarioResult(name=name, passed=False, error=f"setup failed: {e}")
    except Exception as e:
        return ScenarioResult(name=name, passed=False, error=str(e))


def print_result(result: ScenarioResult) -> None:
    status = "PASS" if result.passed else "FAIL"
    print(f"[{status}] {result.name}")
    if result.error:
        print(f"  error: {result.error}")
    for a in result.asserts:
        if not a.passed:
            print(f"  FAIL {a.name}: {a.message}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Orchestra eval runner")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List available scenarios")
    group.add_argument("--scenario", help="Run a specific scenario by name")
    group.add_argument("--all", action="store_true", help="Run all scenarios")
    args = parser.parse_args()

    if args.list:
        scenarios = list_scenarios()
        if not scenarios:
            print("No scenarios found in", SCENARIOS_DIR)
            return 0
        for s in scenarios:
            print(s.stem)
        return 0

    if args.scenario:
        path = SCENARIOS_DIR / f"{args.scenario}.json"
        if not path.exists():
            print(f"Scenario not found: {path}", file=sys.stderr)
            return 1
        result = run_scenario(path)
        print_result(result)
        return 0 if result.passed else 1

    if args.all:
        scenarios = list_scenarios()
        if not scenarios:
            print("No scenarios found")
            return 0
        results = [run_scenario(s) for s in scenarios]
        for r in results:
            print_result(r)
        n_pass = sum(1 for r in results if r.passed)
        print(f"\n{n_pass}/{len(results)} scenarios passed")
        return 0 if n_pass == len(results) else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
