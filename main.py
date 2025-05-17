import json
import os
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class File:
    path: str
    byte_count: int


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

    files: list[File] = []
    for path in file_paths:
        if os.path.exists(path):
            files.append(File(path=path, byte_count=os.stat(path).st_size))

    files = sorted(files, key=lambda file: file.byte_count)

    print("bytes\t\tfile")
    print("-----------------------------")
    for file in files:
        print(f"{file.byte_count}\t\t{file.path}")


if __name__ == "__main__":
    main()
