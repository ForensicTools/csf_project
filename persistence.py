"""
Authors:
Will McDonnell
Michael Milkovich

persistence.py

Aid investigators by providing an easy to read report of potential
signs of persistence on a linux system.
"""

import os
import stat
import time
import pwd
import grp
import re
import requests
from requests.exceptions import ConnectionError
import psutil
from zipfile import ZipFile
from crontab import CronTab


def get_bash_info():
    zip_file = ZipFile('user_bash.zip', 'w')
    # Get system wide bashrc
    if os.path.exists('/etc/bash.bashrc'):
        zip_file.write('/etc/bash.bashrc', arcname='bash.bashrc')
    # All users
    for p in pwd.getpwall():
        user = User(p)
        if os.path.exists(user.dir + '/.bash_profile'):
            zip_file.write(user.dir + '/.bash_profile', arcname=user.username + '_bash_profile')
        if os.path.exists(user.dir + '/.bashrc'):
            zip_file.write(user.dir + '/.bashrc', arcname=user.username + '_bashrc')
    zip_file.close()


def get_chrome_extensions(user):
    extension_names = []
    ext_dir = '/home/{}/.config/google-chrome/Default/Extensions'.format(user.username)
    if os.path.exists(ext_dir):
        extensions = os.listdir(ext_dir)
        try:
            for ext in extensions:
                if ext == 'Temp':
                    continue
                # All extension IDs can be resolved with the below URL, otherwise output ID
                a = requests.get('https://chrome.google.com/webstore/detail/{}'.format(ext), timeout=2)
                if a.status_code == 200:
                    e = re.search(r'<title[^>]*>([^<]+)</title>', a.content.decode())
                    name = e.group()[7:-8]
                    extension_names.append(name)
                else:
                    extension_names.append('Extension ID: {}'.format(ext))
        except ConnectionError as e:
            print("Error: {}".format(e))
            extension_names = extensions
    return extension_names


class Entry:

    def __init__(self, path, hidden_entries, uid_entries, gid_entries, ignore_dir):
        self.ignore_dir = ignore_dir
        self.path = path
        self.error = False
        self.hidden = os.path.basename(path).startswith('.')
        try:
            # Device files and other weird files have issues with stat, can be ignored
            path_stat = os.lstat(path)
        except Exception as e:
            print('error: {}'.format(e))
            return
        self.setuid = path_stat.st_mode & stat.S_ISUID
        self.setgid = path_stat.st_mode & stat.S_ISGID
        self.access_time = time.ctime(path_stat.st_atime)
        self.mod_time = time.ctime(path_stat.st_mtime)
        self.meta_time = time.ctime(path_stat.st_ctime)
        self.is_exec = os.access(path, os.X_OK)

        if self.hidden and self.is_exec:
            hidden_entries.append(self)
        if self.setuid:
            uid_entries.append(self)
        if self.setgid:
            gid_entries.append(self)


class Root:

    def __init__(self, path, hidden_entries, uid_entries, gid_entries, ignore_dir):
        self.entries = []
        for root, dirs, files in os.walk(path, topdown=True):
            dirs[:] = [d for d in dirs if d not in ignore_dir]
            for directory in dirs:
                new_dir = Entry(os.path.join(root, directory), hidden_entries, uid_entries, gid_entries, ignore_dir)
                del new_dir
            for file in files:
                new_file = Entry(os.path.join(root, file), hidden_entries, uid_entries, gid_entries, ignore_dir)
                del new_file
            else:
                continue


class User:
    def __init__(self, p):
        self.username = p[0]
        groups = [g.gr_name for g in grp.getgrall() if self.username in g.gr_mem]
        self.groups = groups
        self.shell = p.pw_shell
        self.dir = p.pw_dir
        self.cron_entries = self.get_cron()

    def get_cron(self):
        entries = []
        user_cron = CronTab(user=self.username)
        for job in user_cron:
            entries.append(job)
        return entries


if __name__ == "__main__":
    if os.getuid() != 0:
        print("Error: Insufficient permissions, run with sudo")
        exit(1)
    report = open('report.txt', 'w')
    hidden_entries = []
    set_uid_entries = []
    set_gid_entries = []
    ignore_directory = ['/proc', '/sys/bus', '/sys/dev', '/sys/devices', '/sys/block', '/sys/class', '/sys/module']
    Root('/', hidden_entries, set_uid_entries, set_gid_entries, ignore_directory)

    std = sorted(hidden_entries, key=lambda file: (os.path.dirname(file.path), os.path.basename(file.path)))
    report.write('===========Hidden Executables===========\n')
    for i in range(0, len(std)):
        if i > 0 and os.path.dirname(std[i].path) != os.path.dirname(std[i - 1].path):
            report.write('\n')
        report.write(std[i].path + ' owner: ' + std[i].owner + '\n')
    report.write('\n')

    std = sorted(set_uid_entries, key=lambda file: (os.path.dirname(file.path), os.path.basename(file.path)))
    report.write('===========SetUID Files===========\n')
    for i in range(0, len(std)):
        if i > 0 and os.path.dirname(std[i].path) != os.path.dirname(std[i - 1].path):
            report.write('\n')
        report.write(std[i].path + ' run as user ' + std[i].owner + '\n')
    report.write('\n')

    std = sorted(set_gid_entries, key=lambda file: (os.path.dirname(file.path), os.path.basename(file.path)))
    report.write('===========SetGID Directories===========\n')
    for i in range(0, len(std)):
        if i > 0 and os.path.dirname(std[i].path) != os.path.dirname(std[i - 1].path):
            report.write('\n')
        report.write(std[i].path + ' run as group ' + std[i].group + '\n')
    report.write('\n')

    get_bash_info()

    report.write('===========Users===========\n')
    for p in pwd.getpwall():
        u = User(p)
        chrome_extensions = get_chrome_extensions(u)
        report.write(u.username+'\n')
        if u.cron_entries:
            report.write('\t-----Scheduled Tasks-----\n')
            for task in u.cron_entries:
                report.write('\t' + str(task)+'\n')
            report.write('\t----------------------------\n')
        if chrome_extensions:
            report.write('\t-----Chrome Extensions-----\n')
            for ext in chrome_extensions:
                report.write('\t' + ext + '\n')
            report.write('\t----------------------------\n')
        if u.groups:
            report.write('\t-----Group Membership-----\n')
            for group in u.groups:
                report.write('\t' + group + '\n')
            report.write('\t----------------------------\n')
    current_users = psutil.users()
    report.write('\n')
    report.write('==========Active Users==========\n')
    report.write('user, terminal, pid, start_time\n')
    for active_user in current_users:
        report.write('{}, {}, {}, {}\n'.format(active_user.name, active_user.terminal, active_user.pid, time.ctime(active_user.started)))
    report.close()
