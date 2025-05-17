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
