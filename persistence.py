#!/usr/bin/sudo python
import os
import stat
import time
import pwd


def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)]


class Entry:

    def __init__(self, path, hidden_entries, uid_entries, gid_entries, ignore_dir):
        self.ignore_dir = ignore_dir
        self.path = path
        self.error = False
        self.hidden = os.path.basename(path).startswith('.')
        try:
            path_stat = os.lstat(path)
        except Exception:
            print('error')
            pass
        self.setuid = path_stat.st_mode & stat.S_ISUID
        self.setgid = path_stat.st_mode & stat.S_ISGID
        self.access_time = time.ctime(path_stat.st_atime)
        self.mod_time = time.ctime(path_stat.st_mtime)
        self.meta_time = time.ctime(path_stat.st_ctime)
        self.owner = pwd.getpwuid(path_stat.st_uid)

        if self.hidden:
            hidden_entries.append(self)
        if self.setuid:
            uid_entries.append(self)
        if self.setgid:
            gid_entries.append(self)


class Directory(Entry):

    def __init__(self, path, hidden_entries, uid_entries, gid_entries, ignore_dir):
        Entry.__init__(self, path, hidden_entries, uid_entries, gid_entries, ignore_dir)
        self.entries = []
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                if full_path in self.ignore_dir:
                    continue
                new_dir = Directory(os.path.join(path, entry), hidden_entries, uid_entries, gid_entries, ignore_dir)
                self.entries.append(new_dir)
            elif os.path.isfile(full_path):
                new_file = File(os.path.join(path, entry), hidden_entries, uid_entries, gid_entries, ignore_dir)
                self.entries.append(new_file)
            else:
                continue


class File(Entry):

    def __init__(self, path, hidden_entries, uid_entries, gid_entries, ignore_dir):
        Entry.__init__(self, path, hidden_entries, uid_entries, gid_entries, ignore_dir)
        self.is_exec = os.access(path, os.X_OK)


class User:
    def __init__(self, p):
        self.username = p[0]
        self.group = grp.getgrgid(p[3])[0]
        self.shell = p.pw_shell
        self.dir = p.pw_dir
        self.cron_entries = self.get_cron()

    def get_cron(self):
        entries = []
        user_cron = CronTab(user=self.username)
        for job in user_cron:
            entries.append(job)
        return entries

hidden_entries = []
uid_entries = []
gid_entries = []
ignore_directory = ['/proc', '/sys/bus', '/sys/dev', '/sys/devices', '/sys/block', '/sys/class', '/sys/module']
# root = Directory('/', hidden_entries, uid_entries, gid_entries, ignore_directory)
# print(len(hidden_entries))
# print(len(uid_entries))
# print(len(gid_entries))
from crontab import CronTab
#mycron = CronTab(user='root')
# job1 = mycron.new(command='touch hello.world')
# job1.minute.every(10)
# mycron.write()
# for job in mycron:
#     mycron.remove(job)
#     mycron.write()

import pwd, grp
for p in pwd.getpwall():
    u = User(p)

