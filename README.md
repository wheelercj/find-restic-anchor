# find-restic-anchor

Find the largest files in your latest [Restic](https://restic.net/) backup.

```
$ python3 find-restic-anchor/main.py
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

Files are ordered by increasing bytes.

Find-restic-anchor is for when a backup is larger than you expect and you want to know why. It only lists files that were added or changed, not files that were removed or unchanged. Also, find-restic-anchor doesn't list files that don't exist locally anymore, and it shows the current local size of the files, not necessarily the size they were when they were backed up.

You could use [`restic ls --long latest --sort size`](https://restic.readthedocs.io/en/stable/045_working_with_repos.html#listing-files-in-a-snapshot) if you want to see the size of every file in the latest snapshot including ones that didn't change, but that won't answer the question of why the latest backup was different.

Find-restic-anchor uses [environment variables](https://restic.readthedocs.io/en/stable/040_backup.html#environment-variables).
