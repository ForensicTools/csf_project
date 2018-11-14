import os
import stat
import time
import pwd
import grp
import re
import requests
from zipfile import ZipFile
from crontab import CronTab


def listdir_fullpath(d):
    return [os.path.join(d, f) for f in os.listdir(d)]


def get_bash_info():
    zip_file = ZipFile('user_bash.zip', 'w')
    if os.path.exists('/etc/bash.bashrc'):
        zip_file.write('/etc/bash.bashrc', arcname='bash.bashrc')
    for p in pwd.getpwall():
        user = User(p)
        if os.path.exists(user.dir + '/.bash_profile'):
            zip_file.write(user.dir + '/.bash_profile', arcname=user.username + '_bash_profile')
        if os.path.exists(user.dir + '/.bashrc'):
            zip_file.write(user.dir + '/.bashrc', arcname=user.username + '_bashrc')
    zip_file.close()


class Entry:

    def __init__(self, path, hidden_entries, uid_entries, gid_entries, ignore_dir):
        self.ignore_dir = ignore_dir
        self.path = path
        self.error = False
        self.hidden = os.path.basename(path).startswith('.')
        try:
            path_stat = os.lstat(path)
        except Exception as e:
            print('error: {}'.format(e))
            pass
        self.setuid = path_stat.st_mode & stat.S_ISUID
        self.setgid = path_stat.st_mode & stat.S_ISGID
        self.access_time = time.ctime(path_stat.st_atime)
        self.mod_time = time.ctime(path_stat.st_mtime)
        self.meta_time = time.ctime(path_stat.st_ctime)
        self.owner = pwd.getpwuid(path_stat.st_uid)[0]
        self.group = grp.getgrgid(path_stat.st_gid)[0]
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
            for dir in dirs:
                new_dir = Entry(os.path.join(root, dir), hidden_entries, uid_entries, gid_entries, ignore_dir)
                del new_dir
            for file in files:
                new_file = Entry(os.path.join(root, file), hidden_entries, uid_entries, gid_entries, ignore_dir)
                del new_file
            else:
                continue


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


if __name__ == "__main__":
    report = open('report.txt', 'w')
    hidden_entries = []
    set_uid_entries = []
    set_gid_entries = []
    ignore_directory = ['/proc', '/sys/bus', '/sys/dev', '/sys/devices', '/sys/block', '/sys/class', '/sys/module']
    root = Root('/home/will/PycharmProjects', hidden_entries, set_uid_entries, set_gid_entries, ignore_directory)

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
        if i > 0 and os.path.dirname(std[i]) != os.path.dirname(std[i - 1]):
            report.write('\n')
        report.write(std[i].path + ' run as user ' + std[i].owner + '\n')
    report.write('\n')

    std = sorted(set_gid_entries, key=lambda file: (os.path.dirname(file.path), os.path.basename(file.path)))
    report.write('===========SetGID Directories===========\n')
    for i in range(0, len(std)):
        if i > 0 and os.path.dirname(std[i]) != os.path.dirname(std[i - 1]):
            report.write('\n')
        report.write(std[i].path + ' run as group ' + std[i].group + '\n')
    report.write('\n')

    get_bash_info()
    extensions = get_chrome_extensions()
    for ext in extensions:
        a = requests.get('https://chrome.google.com/webstore/detail/aapocclcgogkmnckokdopfmhonfmgoek')
        e = re.search(r'<title[^>]*>([^<]+)</title>', a.content.decode())
        name = e.group()
    # mycron = CronTab(user='root')
    # job1 = mycron.new(command='touch hello.world')
    # job1.minute.every(10)
    # mycron.write()
    report.write('===========Users===========\n')
    for p in pwd.getpwall():
        u = User(p)
        report.write(u.username+'\n')
        if u.cron_entries:
            report.write('-----Scheduled Tasks-----\n')
            for task in u.cron_entries:
                report.write(str(task)+'\n')
            report.write("\n")
    report.close()

