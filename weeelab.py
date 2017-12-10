#!/usr/bin/python3

"""
WEEELAB - Log management module for garbaging paper sign sheet.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import json
from datetime import datetime
from datetime import timedelta
import sys

__version__ = "2.2"
__author__ = "Stefano Enrico Mendola (aka Hyd3L)"
__maintainer__ = "WeeeOpen team"

EXECNAME = os.path.basename(__file__)  # name of this file

# Disable owncloud uploads during debug sessions
debuggingState = False

# multi platform support ######################################################
if sys.platform == 'linux':
    from socket import gethostname
    import pwd

    HOSTNAME = gethostname()  # "schifomacchina"
    UID = os.getuid()
    if UID == 0:  # root execution check
        raise PermissionError("can't execute " + EXECNAME + " as root.")
    HOSTUSER = pwd.getpwuid(UID).pw_name  # "weeeopen"
    LOG_PATH = "/home/{}/.local/share/{}/log.dat".format(HOSTUSER, HOSTNAME)
    USERS_PATH = "/home/{}/.local/share/{}/users.json".format(HOSTUSER,
                                                              HOSTNAME)
    BACKUP_PATH = "/home/{}/ownCloud/weeeopen/{}/".format(HOSTUSER, HOSTNAME)
elif sys.platform == 'win32':  # only for tests
    debuggingState = True
    HOSTNAME = "testmachine"
    HOSTUSER = "developer"
    LOG_PATH = os.path.dirname(os.path.realpath(__file__)) + "/log.dat"
    USERS_PATH = os.path.dirname(os.path.realpath(__file__)) + "/users.json"
    BACKUP_PATH = os.path.dirname(os.path.realpath(__file__)) + "/backup/"
else:
    raise EnvironmentError('OS not supported')


class LogRow:
    """
    LogRow -  row of log.dat
    '%Y-%m-%d %H:%M - %H:%M - username - workdone'

    time_in : <datetime> datetime.now()
    time_work : <timedelta> = 'INLAB'
    username : <string> = '__user__'
    workdone : <string> = ''
    """
    sep = ' - '
    mask_datetime = '%Y-%m-%d %H:%M'
    presence = 'INLAB'

    def __init__(self, row=''):
        if row == '':
            self.time_in = datetime.now()
            self.time_work = self.presence
            self.username = '__user__'
            self.workdone = ''
        else:
            self.time_in = datetime.strptime(row.split(self.sep)[0].strip(),
                                             self.mask_datetime)
            td = row.split(self.sep)[1].strip()
            if td == self.presence:
                self.time_work = self.presence
            else:
                self.time_work = timedelta(hours=int(td.split(':')[0]),
                                           minutes=int(td.split(':')[1]))
            self.username = row.split(self.sep)[2].strip()
            self.workdone = self.sep.join(row.split(self.sep)[3:]).strip()

    def __repr__(self):
        if self.inlab():
            tm = self.presence
        else:
            seconds = self.time_work.total_seconds()
            hh = str(int(seconds // 3600)).zfill(2)
            mm = str(int((seconds % 3600) // 60)).zfill(2)
            tm = hh + ':' + mm
        return self.sep.join((self.time_in.strftime(self.mask_datetime),
                              tm, self.username, self.workdone)) + '\n'

    def inlab(self, username=''):
        """
        Return True if <username> is logged in else False
        :param username: 'Name Surname'
        :return: bool
        """
        if username:
            return (self.time_work == self.presence) and (
                    self.username == username)
        else:
            return self.time_work == self.presence

    def logout(self, workdone):
        """
        Set time_work, workdone and return True if success else return False
        :param workdone: string
        :return: bool
        """
        if self.inlab():
            self.time_work = datetime.now() - self.time_in
            self.workdone = workdone
            return True
        return False


# Colors for Terminal
COLOR_RED = "\033[1;31m"
COLOR_STANDARD = "\033[;7m"
COLOR_NATIVE = "\033[m"


# terminate the program being sure about undoing some changes like cli color
def secure_exit(value=0):
    sys.stdout.write(COLOR_NATIVE)
    sys.exit(value)


def __p_host(string=''):
    print(HOSTNAME + ': ' + string)


def __p_usage(string=''):
    print('usage: ' + EXECNAME + ' ' + string)


def help(cmd=''):
    if cmd == "login":
        __p_usage("login <username>")
        __p_host("Username format is 'first.last' or 'XXXXXX'")
        print("                where XXXXXX is your serial number.")
        print("                You can even use an alias if defined.")
        secure_exit()

    elif cmd == "logout":
        __p_usage("logout <username>")
        __p_host("Username format is 'first.last'")
        print("                where XXXXXX is your serial number.")
        print("                You can even use an alias if defined.")
        secure_exit()

    elif cmd == "show":
        __p_usage("show <option>")
        print("  available options:")
        print("      log : Print log file to stdout.")
        print("    inlab : View a list of students in lab now.")
        secure_exit()

    elif cmd == "stat":
        __p_usage("stat <username>")
        __p_host("If you want to view stats for everybody,")
        print("                use \"" + EXECNAME + " stat all\"")

    elif cmd == "top":
        __p_usage("top <list_length>")

    else:
        print(
            "WEEELAB v" + __version__ + " - Log management module for garbaging paper sign sheet.")
        print(
            "Author: Stefano Enrico Mendola (aka Hyd3L, STE col teschio)")
        print("Copyright (C) 2017 WeeeOpen - Politecnico di Torino")
        print("This program comes with ABSOLUTELY NO WARRANTY.")
        print("Since this is a free software, you are welcome")
        print("to redistribute it under the terms of the GNU GPLv3.\n")
        print("  Available commands:")
        print("    login  <username> : Sign access to the lab.")
        print("    logout <username> : Sign quit from the lab.")
        print("    show   <option>   : Retrieve informations.")
        print(
            "    stat   <username> : Compute stats for a user or for all users.")
        print(
            "    top <list_length> : Show a list of top <list_length> members.")
        secure_exit()


# check if the passed date is in the right format
def checkDate(input):
    date = input.split("/")

    if len(date[0]) != 2 or len(date[1]) != 2 or len(date[2]) != 4:
        print("date format error")
        secure_exit(2)
    return input


def checkHour(input):
    hour = input.split(":")
    if len(hour) != 2:
        print("wrong hour format")
        secure_exit(2)
    return input


def check_user(username):
    """
    Check if an username exists in users list file.
    :param username: string
    :return: 'Name Surname' -> of that username
             '' -> username don't exist
    """
    username = username.replace('.', ' ').lower()
    with open(USERS_PATH) as usersFile:
        users_dict = json.load(usersFile)
    for user in users_dict['users']:
        uns = [(user['name'] + ' ' + user['surname']).lower(),
               user['serial'], user['nickname'].lower()]
        if username in uns:
            return user['name'] + ' ' + user['surname']
    return ''  # if user not found


def get_inlab():
    """
    Get the list of logged in users
    :return: list of string -> all users in lab
             [] -> nobody is in lab
    """
    users_in_lab = []
    with open(LOG_PATH) as logFile:
        for line in logFile:
            lr = LogRow(line)
            if lr.inlab():
                users_in_lab.append(lr.username)
    return users_in_lab


def is_inlab(username):
    """
    Check if <username> is in lab
    :param username: string
    :return: True -> user is in lab
             False -> user isn't in lab
    """
    users_inlab = get_inlab()
    username = check_user(username)
    for user in users_inlab:
        if user == username:
            return True
    return False


def login(username):
    """
    Write a new LogRow in log file
    :param username: string
    :return: 0, 'Name Surname' -> Login success
             1, '' -> username don't exist
             2, 'Name Surname' -> user isn't in lab
    """
    username = check_user(username)
    if username:
        if is_inlab(username):
            return 2, username
        else:
            lg = LogRow()
            lg.username = username
            with open(LOG_PATH, 'a') as logFile:
                logFile.write(repr(lg))
            if not debuggingState:  # Send to ownCloud folder
                os.system("cp " + LOG_PATH + " " + BACKUP_PATH + "log.txt")
            return 0, username
    return 1, username


def write_logout(username, workdone):
    found = False
    logList = []
    with open(LOG_PATH) as logFile:
        # si salva tutto il file nella lista, se trova la voce che contiene
        # INLAB e username del logout modifica quella stringa
        for line in logFile:
            lr = LogRow(line)
            if lr.inlab(username):
                found = True
                lr.logout(workdone)
            logList.append(repr(lr))  # Store everything in the list

    if found:
        # Writing everything to log file
        with open(LOG_PATH, 'w') as logFile:
            for line in logList:
                logFile.write(line)
        if not debuggingState:
            # Send to ownCloud folder
            os.system("cp " + LOG_PATH + " " + BACKUP_PATH + "log.txt")
        print(
            HOSTNAME + ": Logout successful! Bye " + username + "!")
    else:
        print(HOSTNAME + ": " + username + " is not in lab!")


def logout(username):
    username = check_user(username)

    if is_inlab(username):
        try:
            workdone = input(HOSTNAME + ": What have you done?\n:: ")
            while len(workdone) > 128:
                print(
                    HOSTNAME + ": I didn't ask you the story of your life!")
                workdone = input(
                    HOSTNAME + ": What have you done? [BRIEFLY]\n>> ")
            write_logout(username, workdone)
        except KeyboardInterrupt:
            print(
                HOSTNAME + ": Logout fail! Sorry " + username + "!")
    else:
        print(HOSTNAME + ": " + username + " is not in lab!")


# logout by passing manually date and time
def manualLogout():
    tmpUsr = input("ADMIN--> insert username: ")
    username = check_user(tmpUsr)

    tmpDate = input("ADMIN--> insert date (gg/mm/aaaa): ")
    date = checkDate(tmpDate)

    tmpH = input("ADMIN--> insert time (hh:mm): ")
    hour = checkHour(tmpH)

    currTime = hour

    workdone = input(HOSTNAME + ": What have you done?\n:: ")
    while len(workdone) > 128:
        print(HOSTNAME + ": I didn't ask you the story of your life!")
        workdone = input(HOSTNAME + ": What have you done? [BRIEFLY]\n>> ")

    print("ADMIN--> you will update the log file with ")
    print("            " + username + " " + currTime)
    answer = input("ADMIN--> are you sure? (y/n)")
    if answer != "y":
        secure_exit()

    write_logout(username, workdone)


def show(option):
    if option == "log":
        print(HOSTNAME + ": Reading log file...\n")
        with open(LOG_PATH) as logFile:
            for line in logFile:
                print(line.replace('\n', ''))

    elif option == "inlab":
        users_in_lab = get_inlab()
        count = len(users_in_lab)
        print(HOSTNAME + ": Reading log file...\n")
        for user in users_in_lab:
            print("> " + user)
        if count == 0:
            print(HOSTNAME + ": Nobody is in lab right now.")
        elif count == 1:
            print(HOSTNAME + ": There is one student in lab right now.")
        else:
            print(
                HOSTNAME + ": There are {c} students in lab right now.".format(
                    c=count))

    elif option == "help":
        help()

    else:
        print("error: option " + option + " is not defined.")


# Returns total work time in minutes
def totWorkTime(username):
    timeSpent = 0
    logFile = open(LOG_PATH, "r")
    for line in logFile:
        if (username in line) and not ("INLAB" in line):
            timeSpent += ((int(line[39:41]) * 60) + int(line[42:44]))
    logFile.close()
    return timeSpent


# Convert minutes in a formatted string
def timeConv(minutes):
    return str(minutes / 60) + "h " + str(minutes % 60) + "m"


def stat(username):
    print(HOSTNAME + ": Computing stats...\n")
    currMonth = datetime.now().strftime(" [%B %Y]")

    # Compute stats for all users (Extremely stupid algorithm, but works fine)
    if username == "all":
        usersFile = open(USERS_PATH, "r")
        for line in usersFile:
            currUser = line.split()[0]
            print("[+]     Name: " + currUser)
            print("[+] WorkTime: " + timeConv(
                totWorkTime(currUser)) + currMonth + "\n")
        usersFile.close()

    else:
        username = check_user(username)
        print("[+]     Name: " + username)
        print(
            "[+] WorkTime: " + timeConv(totWorkTime(username)) + currMonth)


# Print users list ordered by most active first.
def top(length):
    usersList = [(int, str)]
    usersFile = open(USERS_PATH, 'r')

    # Loading usernames from file
    for line in usersFile:
        usersList.append((0, line.split()[0].replace("\n", '')))
    usersFile.close()
    usersList.remove((int, str))

    # Computing total work time for each member
    for i in range(0, len(usersList)):
        user = usersList[i]
        user = (totWorkTime(user[1]),) + user[1:]
        usersList[i] = user
    usersList.sort(reverse=True)

    print(HOSTNAME + ": Hall of Fame\n")
    count = 1
    for i in range(0, length):
        if len(usersList) <= i:
            break
        print("[" + str(count).zfill(2) + "] " + usersList[i][1])
        count += 1


def main(args):
    if len(args) < 2:
        print("usage: " + EXECNAME + " <command> <arguments>")
        secure_exit()
    command = args[1]

    # Add commands here
    if command == "help":
        if len(args) < 3:
            help()
        elif len(args) >= 3:
            help(args[2])
    elif command == "login":
        if len(args) != 3:
            __p_usage("login <username>")
            secure_exit()
        else:
            r, username = login(args[2])
            if r == 0:
                __p_host("Login successful! Hello " + username + "!")
            elif r == 1:
                print("error: Username not recognized.")
                __p_host("Maybe you misspelled it or you're an intruder.")
            elif r == 2:
                __p_host(username + ", you're already logged in.")
    elif command == "logout":
        if len(args) != 3:
            __p_usage("logout <username>")
            secure_exit()
        else:
            logout(args[2])

    elif command == "show":
        if len(args) != 3:
            print("usage: " + EXECNAME + " show <option>")
            print("  available options:")
            print("      log : Print log file to stdout.")
            print("    inlab : View a list of students in lab now.")
            secure_exit()
        else:
            show(args[2])

    elif command == "stat":
        if len(args) != 3:
            print("usage: " + EXECNAME + " stat <username>")
            secure_exit()
        else:
            stat(args[2])

    elif command == "top":
        if len(args) == 3:
            if args[2].isdigit is False:
                print("usage: " + EXECNAME + " top <list_length>")
            else:
                top(int(args[2]))
        else:
            top(10)
    elif command == "admin":
        sys.stdout.write(COLOR_RED)
        print("WARNING: be sure of what you will do!")
        if len(args) != 3:
            # print("usage: "+EXECNAME+" admin <login/logout>")
            print("usage: " + EXECNAME + " admin <logout>")
            secure_exit()
        else:
            manualLogout()
            sys.stdout.write(COLOR_NATIVE)
    else:
        print("error: Invalid command detected -> " + args[1])
        print(HOSTNAME + ": Try with \"" + EXECNAME + " help\"")


def sanity_check():
    # Check if LOG_PATH exist, if False make it
    if not os.path.isfile(LOG_PATH):
        with open(LOG_PATH, 'x'):
            print(HOSTNAME + ": New log file was created.")
    # se è un nuovo mese rinomina log.dat in log%Y-%m.dat e ne crea una copia
    with open(LOG_PATH) as logFile:
        last_date = LogRow(logFile.readline()).time_in

    last_month, last_year = last_date.month, last_date.year
    curr_date = datetime.now()
    curr_month, curr_year = curr_date.month, curr_date.year
    if (curr_month > last_month) or (curr_year > last_year):
        print(HOSTNAME + ": Backing up log file... ")
        file_ext = os.path.splitext(LOG_PATH)[1]
        new_path = LOG_PATH[:-len(file_ext)] + last_date.strftime(
            '%Y-%m') + file_ext
        os.rename(LOG_PATH, new_path)
        if not debuggingState:
            # Send to ownCloud folder
            os.system("cp " + new_path + " " + BACKUP_PATH +
                      "log" + last_date.strftime('%Y-%m') + ".txt")
        if not os.path.isfile(LOG_PATH):
            with open(LOG_PATH, 'x'):
                print(HOSTNAME + ": New log file was created.")
        print("Done!")
    # Check if users list file exists.
    if not os.path.isfile(USERS_PATH):
        print("error: Users list not found.")
        secure_exit(2)


sanity_check()
if __name__ == '__main__':
    main(sys.argv)
