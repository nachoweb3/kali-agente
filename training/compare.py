"""Paired comparison of independently verified held-out tasks, with exact sign test."""

import argparse
import json
import math
from pathlib import Path


def compare(baseline, candidate):
    keys = (
        "suite_sha256",
        "runner_sha256",
        "budget_seconds",
        "action_limit",
        "context",
        "output_tokens",
        "seed",
        "backend",
        "hardware",
        "deployment_schema_sha256",
    )
    for key in keys:
        if key not in baseline["conditions"] or baseline["conditions"][key] != candidate[
            "conditions"
        ].get(key):
            raise ValueError("Non-comparable condition: " + key)
    for run in (baseline, candidate):
        if not run.get("model_digest"):
            raise ValueError("Model/adapter digest required")
        if len({r["id"] for r in run["tasks"]}) != len(run["tasks"]):
            raise ValueError("Duplicate task identifiers")
        for row in run["tasks"]:
            if (
                not isinstance(row.get("passed"), bool)
                or not isinstance(row.get("seconds"), (int, float))
                or not math.isfinite(row["seconds"])
                or row["seconds"] < 0
            ):
                raise ValueError("Invalid task result")
            if row.get("split") != "test" or row.get("training_overlap") is not False:
                raise ValueError("Evaluation requires held-out test tasks without training overlap")
            if not row.get("verification_sha256"):
                raise ValueError("Independent verification artifact digest required")
    left, right = ({r["id"]: r for r in run["tasks"]} for run in (baseline, candidate))
    if not left or left.keys() != right.keys():
        raise ValueError("Both models must complete the same task set, including failures/timeouts")
    wins = sum(not left[k]["passed"] and right[k]["passed"] for k in left)
    losses = sum(left[k]["passed"] and not right[k]["passed"] for k in left)
    n, discordant = len(left), wins + losses
    p = (
        min(
            1.0,
            2 * sum(math.comb(discordant, i) for i in range(min(wins, losses) + 1)) / 2**discordant,
        )
        if discordant
        else 1.0
    )
    delta = (wins - losses) / n
    return {
        "tasks": n,
        "baseline_passed": sum(r["passed"] for r in left.values()),
        "candidate_passed": sum(r["passed"] for r in right.values()),
        "wins": wins,
        "regressions": losses,
        "absolute_gain": delta,
        "paired_exact_two_sided_p": p,
        "promotion_gate_passed": n >= 30 and delta >= 0.10 and p < 0.05 and losses == 0,
        "note": "Gate is a project policy, not proof of general expertise. Requires authentic independent artifacts; digests alone do not prove their validity.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    opts = parser.parse_args()
    print(
        json.dumps(
            compare(json.loads(opts.baseline.read_text()), json.loads(opts.candidate.read_text())),
            indent=2,
        )
    )
