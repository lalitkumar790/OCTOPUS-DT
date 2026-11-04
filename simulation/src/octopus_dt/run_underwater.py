"""Run a small deterministic MuJoCo trajectory and save generalized state."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import mujoco
import numpy as np

from .model import load_model


def run(steps: int, output: Path) -> None:
    if steps < 1:
        raise ValueError("steps must be positive")
    model, data = load_model()
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time_s", "qpos_norm", "qvel_norm", "energy_proxy"])
        for _ in range(steps):
            mujoco.mj_step(model, data)
            energy = float(data.energy[0] + data.energy[1])
            writer.writerow([f"{data.time:.6f}", float(np.linalg.norm(data.qpos)),
                             float(np.linalg.norm(data.qvel)), energy])
    print(f"Wrote {steps} rows to {output}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=2000)
    parser.add_argument("--output", type=Path, default=Path("research/datasets/run.csv"))
    args = parser.parse_args()
    run(args.steps, args.output)


if __name__ == "__main__":
    main()
