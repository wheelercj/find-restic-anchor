import argparse
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


snapshot_id_1: str = ""
snapshot_id_2: str = ""
human_readable: bool = False


def parse_args():
    global snapshot_id_1
    global snapshot_id_2
    global human_readable

    global total_steps

    parser = argparse.ArgumentParser(
        prog="find-restic-anchor",
        description="""
            find-restic-anchor can help you figure out why a Restic backup took longer than normal
            by listing only the files that were added or changed in a snapshot, and their sizes.
            Files are ordered by increasing bytes. More details:
            https://github.com/wheelercj/find-restic-anchor
            """,
    )

    parser.add_argument("snapshot_id_1", type=str, nargs="?")
    parser.add_argument("snapshot_id_2", type=str, nargs="?")

    parser.add_argument(
        "--human-readable", action="store_true", help="print sizes in human readable format"
    )

    args = parser.parse_args()

    snapshot_id_1 = args.snapshot_id_1
    snapshot_id_2 = args.snapshot_id_2
    if bool(snapshot_id_1) != bool(snapshot_id_2):
        print("Error: expected zero or two snapshot IDs, not one", file=sys.stderr)
        sys.exit(1)
    elif snapshot_id_1 and snapshot_id_2:
        if "latest" == snapshot_id_1 or "latest" == snapshot_id_2:
            print("Error: the special snapshot ID `latest` is not supported", file=sys.stderr)
            sys.exit(1)
        total_steps = 7
    else:
        total_steps = 9

    human_readable = args.human_readable


def main():
    global snapshot_id_1
    global snapshot_id_2

    parse_args()

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
        print("".join(err_msg), file=sys.stderr)
        sys.exit(1)

    if not snapshot_id_1 or not snapshot_id_2:
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
            print(
                "\nError: this script only works when there are at least 2 snapshots",
                file=sys.stderr,
            )
            sys.exit(1)

        snapshot_id_1 = snapshots[-2]["id"]
        snapshot_id_2 = snapshots[-1]["id"]

    print_status("Getting the difference between the snapshots...")
    try:
        diff_result: subprocess.CompletedProcess = subprocess.run(
            ["restic", "diff", snapshot_id_1, snapshot_id_2, "--json"],
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
        if entry["modifier"] == "-":  # ignore files that were removed in the snapshot
            continue

        diff_file_paths.append(Path(entry["path"]))

    print_status("Getting the snapshot's files and folders...")
    try:
        ls_result: subprocess.CompletedProcess = subprocess.run(
            ["restic", "ls", snapshot_id_2, "--long", "--json"],
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

    print_status("Getting the size of each file in the snapshot...")
    snapshot_files_sizes: dict[Path, int] = dict()
    for ls_line in ls_lines:
        line_dict: dict[str, Any] = json.loads(ls_line)
        if "path" not in line_dict:
            # It's not a file or folder. It might be a snapshot summary.
            continue

        path: Path = Path(line_dict["path"])

        if "size" in line_dict:
            snapshot_files_sizes[path] = line_dict["size"]
        else:
            # It's a folder. Even empty folders take up some space, but it's close enough to 0 that
            # it shouldn't matter in this case.
            snapshot_files_sizes[path] = 0

    print_status("Getting the size of each file in the diff...")
    files: list[File] = []
    for diff_path in diff_file_paths:
        files.append(
            File(
                path=diff_path,
                byte_count=snapshot_files_sizes[diff_path],
            )
        )

    print_status("Sorting the files by size...")
    files = sorted(files, key=lambda file: file.byte_count)

    total_byte_count: int = 0

    print(end="\r                                                                              \r")
    print("bytes\t\tfile")
    print("-----------------------------")
    if human_readable:
        for file in files:
            byte_count: str = humanize(file.byte_count)
            if len(byte_count) >= 8:
                print(f"{byte_count}\t{file.path}")
            else:
                print(f"{byte_count}\t\t{file.path}")
            total_byte_count += file.byte_count
    else:
        for file in files:
            print(f"{file.byte_count}\t\t{file.path}")
            total_byte_count += file.byte_count

    print("-----------------------------")
    if human_readable:
        print(f"Total: {humanize(total_byte_count)}")
    else:
        print(f"Total: {total_byte_count} bytes")


step: int = 1
total_steps: int = 9


def print_status(msg: str) -> None:
    global step

    print(
        end=(
            "\r                                                                                 \r"
            + f"({step}/{total_steps}) "
            + msg
        )
    )

    step += 1


def humanize(byte_count: int) -> str:
    if byte_count < 2**10:
        return f"{byte_count} B"
    elif byte_count < 2**20:
        kib: float = byte_count / (2**10)
        return f"{kib:.3f} KiB"
    elif byte_count < 2**30:
        mib: float = byte_count / (2**20)
        return f"{mib:.3f} MiB"
    elif byte_count < 2**40:
        gib: float = byte_count / (2**30)
        return f"{gib:.3f} GiB"
    elif byte_count < 2**50:
        tib: float = byte_count / (2**40)
        return f"{tib:.3f} TiB"
    elif byte_count < 2**60:
        pib: float = byte_count / (2**50)
        return f"{pib:.3f} PiB"
    elif byte_count < 2**70:
        eib: float = byte_count / (2**60)
        return f"{eib:.3f} EiB"
    else:
        return "∞"


if __name__ == "__main__":
    main()
