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

Files are sorted by increasing bytes.

Find-restic-anchor is for when a backup takes longer and/or is larger than you expect and you want to know why. It only lists files that were added or changed, and not files that were removed by the backup. Also, find-restic-backup doesn't list files that don't exist anymore, and it shows the current size of the files, not the size they were when they were backed up.

You could use `restic ls --long latest` if you want to see the size of every file in the latest snapshot including ones that didn't change, but that list will probably be many times longer.
