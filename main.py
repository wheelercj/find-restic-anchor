import json
import os
import subprocess
from typing import Any


def main():
    assert os.environ["RESTIC_REPOSITORY"]
    assert os.environ["RESTIC_PASSWORD"]

    try:
        snapshots_result: subprocess.CompletedProcess = subprocess.run(
            ["restic", "snapshots", "--json"],
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as err:
        if err.returncode == 1:
            raise RuntimeError(json.loads(err.stderr)["message"])
        raise
    if snapshots_result.stderr:
        raise ValueError(f"`restic snapshots` gave a truthy stderr: {snapshots_result.stderr}")

    try:
        snapshots: list[dict[str, Any]] = json.loads(snapshots_result.stdout)
    except json.decoder.JSONDecodeError:
        raise RuntimeError(f"Failed to decode JSON. {snapshots_result.stdout = }")
    last_id: str = snapshots[-1]["id"]
    second_to_last_id: str = snapshots[-2]["id"]

    try:
        diff_result: subprocess.CompletedProcess = subprocess.run(
            ["restic", "diff", second_to_last_id, last_id, "--json"],
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as err:
        if err.returncode == 1:
            raise RuntimeError(json.loads(err.stderr)["message"])
        raise
    if diff_result.stderr:
        raise ValueError(f"`restic diff` gave a truthy stderr: {diff_result.stderr}")

    diff_lines: list[str] = diff_result.stdout.strip().splitlines()

    file_paths: list[str] = []
    for line in diff_lines:
        entry: dict[str, str] = json.loads(line)
        if entry["message_type"] != "change":
            continue
        if entry["modifier"] == "-":
            continue

        file_paths.append(entry["path"])

    largest_size: int = 0
    largest_path: str = "(none)"
    for path in file_paths:
        size: int = os.stat(path).st_size
        if size > largest_size:
            largest_size = size
            largest_path = path

    print(f"{largest_path}\n{largest_size} bytes")


if __name__ == "__main__":
    main()
