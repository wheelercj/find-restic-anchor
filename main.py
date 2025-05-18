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
    assert "RESTIC_REPOSITORY" in os.environ
    assert "RESTIC_PASSWORD" in os.environ
    # more environment variables are necessary, but which ones depends on how you use Restic

    # get the snapshots
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

    assert isinstance(snapshots_result.stdout, bytes), f"{type(snapshots_result.stdout) = }"
    snapshots_s: str = snapshots_result.stdout.decode()

    # convert the string of snapshots to a list of dictionaries
    try:
        snapshots: list[dict[str, Any]] = json.loads(snapshots_s)
    except json.decoder.JSONDecodeError:
        raise RuntimeError(f"Failed to decode JSON. {snapshots_s = }")
    
    # get the IDs of the last two snapshots
    last_id: str = snapshots[-1]["id"]
    second_to_last_id: str = snapshots[-2]["id"]

    # get the difference between the last two snapshots
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

    assert isinstance(diff_result.stdout, bytes), f"{type(diff_result.stdout) = }"
    diff_lines: list[str] = diff_result.stdout.decode().strip().splitlines()

    # get the paths of all new and modified files
    file_paths: list[str] = []
    for line in diff_lines:
        entry: dict[str, str] = json.loads(line)
        if entry["message_type"] != "change":
            continue
        if entry["modifier"] == "-":  # ignore files that were removed in the latest snapshot
            continue

        file_paths.append(entry["path"])

    # get the byte count of each file
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
