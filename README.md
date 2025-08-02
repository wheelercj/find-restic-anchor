# find-restic-anchor

When a [Restic](https://restic.net/) backup takes longer than you expect, find-restic-anchor can help you figure out why by showing the size of each new and modified file in the snapshot.

```bash
$ find-restic-anchor
bytes       file
-----------------------------
0           /home/chris/Documents/programming/GitHub-bot/utils/__init__.py
24          /home/chris/Documents/programming/GitHub-bot/.git/HEAD
41          /home/chris/Documents/programming/GitHub-bot/.git/ORIG_HEAD
41          /home/chris/Documents/programming/GitHub-bot/.git/refs/heads/develop

...

83973       /home/chris/Documents/backups/tasks/2025-05-16_01-55-15_todoist_backup.json
107804      /home/chris/Documents/programming/GitHub-bot/uv.lock
157685      /home/chris/Documents/programming/GitHub-bot/.git/logs/HEAD
625609      /home/chris/Documents/backups/calendars/2025-05-16-Calendar.ics
5242880     /home/chris/Documents/backups/Firefox bookmarks/2025-05-16-places.sqlite
```

Files are ordered by increasing bytes. If you don't enter two snapshot IDs, the latest two snapshots will be used. This script uses [environment variables](https://restic.readthedocs.io/en/stable/040_backup.html#environment-variables).

Find-restic-anchor only lists files that were added or changed, not files that were removed or unchanged. You could use [`restic ls latest --long --sort size`](https://restic.readthedocs.io/en/stable/045_working_with_repos.html#listing-files-in-a-snapshot) if you want to see the size of every file in the latest snapshot including ones that didn't change, but that won't answer the question of why the backup was different.

Large files being backed up is not the only possible reason a backup took longer than normal, but this script can rule out the possibility if nothing else.

## Install

3 ways to install:

- Download or copy [main.py](https://github.com/wheelercj/find-restic-anchor/blob/main/main.py) and run it.
- `uv tool install git+https://github.com/wheelercj/find-restic-anchor@main` and then `find-restic-anchor`
- `git clone https://github.com/wheelercj/find-restic-anchor.git` and then `python3 find-restic-anchor/main.py`

There are no 3rd party dependencies except that a `restic` command must exist.

## How does it work?

If you enter two snapshot IDs, the first few steps below are skipped.

1. `restic snapshots --json` to get the list of snapshots
2. From the list of snapshots, get the IDs of the last two snapshots
3. `restic diff --json` with those two IDs to get the changes made in the second snapshot
4. From the diff, get the paths of files that were added or modified
5. `restic ls <second_snapshot_id> --long --json` to get the second snapshot's file paths and sizes
6. Using those two sets of paths, get the size of each file added or modified in the second snapshot
7. Order the paths by increasing file size
8. Print the paths and sizes
