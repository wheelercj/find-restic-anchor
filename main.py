import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class File:
    path: Path
    byte_count: int


def main():
    has_repo: bool = "RESTIC_REPOSITORY" in os.environ or "RESTIC_REPOSITORY_FILE" in os.environ
    has_password: bool = "RESTIC_PASSWORD" in os.environ or "RESTIC_PASSWORD_FILE" in os.environ
    if not has_repo or not has_password:
        err_msg: list[str] = ["Error: you must define environment variables including"]
        if not has_repo:
            err_msg.append(" (either RESTIC_REPOSITORY or RESTIC_REPOSITORY_FILE)")
        if not has_repo and not has_password:
            err_msg.append(" and")
        if not has_password:
            err_msg.append(" (either RESTIC_PASSWORD or RESTIC_PASSWORD_FILE)")
        err_msg.append(". Other environment variables are also necessary, but which ones depends")
        err_msg.append(" on how you use Restic. For more details, see")
        err_msg.append(
            " https://restic.readthedocs.io/en/stable/040_backup.html#environment-variables"
        )
        print("".join(err_msg))
        sys.exit(1)

    print_status("Getting the list of snapshots...")
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

    print_status("Loading snapshots list JSON...")
    try:
        snapshots: list[dict[str, Any]] = json.loads(snapshots_s)
    except json.decoder.JSONDecodeError:
        raise RuntimeError(f"Failed to decode JSON. {snapshots_s = }")

    # get the IDs of the last two snapshots
    if len(snapshots) < 2:
        print("Error: this script only works when there are at least 2 snapshots")
        sys.exit(1)
    last_id: str = snapshots[-1]["id"]
    second_to_last_id: str = snapshots[-2]["id"]

    print_status("Getting the difference between the last two snapshots...")
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

    print_status("Getting the paths of all new and modified files and folders...")
    diff_file_paths: list[Path] = []
    for line in diff_lines:
        entry: dict[str, str] = json.loads(line)
        if entry["message_type"] != "change":
            continue
        if entry["modifier"] == "-":  # ignore files that were removed in the latest snapshot
            continue

        diff_file_paths.append(Path(entry["path"]))

    print_status("Getting the latest snapshot's files and folders...")
    try:
        ls_result: subprocess.CompletedProcess = subprocess.run(
            ["restic", "ls", "latest", "--long", "--json"],
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as err:
        if err.returncode == 1:
            raise RuntimeError(json.loads(err.stderr)["message"])
        raise
    if ls_result.stderr:
        raise ValueError(f"`restic ls` gave a truthy stderr: {ls_result.stderr}")

    assert isinstance(ls_result.stdout, bytes), f"{type(ls_result.stdout) = }"
    ls_lines: list[str] = ls_result.stdout.decode().strip().splitlines()

    print_status("Getting the size of each file in the latest snapshot...")
    snapshot_files: dict[Path, int] = dict()
    for ls_line in ls_lines:
        file_obj: dict[str, Any] = json.loads(ls_line)
        if "path" not in file_obj:
            continue

        if "size" in file_obj:
            snapshot_files[Path(file_obj["path"])] = file_obj["size"]
        else:
            snapshot_files[Path(file_obj["path"])] = 0

    print_status("Getting the size of each file in the diff...")
    files: list[File] = []
    for diff_path in diff_file_paths:
        files.append(File(path=diff_path, byte_count=snapshot_files[diff_path]))

    print_status("Sorting the files by size...")
    files = sorted(files, key=lambda file: file.byte_count)

    print(end="\r                                                                              \r")
    print("bytes\t\tfile")
    print("-----------------------------")
    for file in files:
        print(f"{file.byte_count}\t\t{file.path}")


step: int = 1


def print_status(msg: str) -> None:
    global step

    print(
        end=(
            "\r                                                                                 \r"
            + f"({step}/9) "
            + msg
        )
    )

    step += 1


if __name__ == "__main__":
    main()
