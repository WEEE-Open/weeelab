#!/usr/bin/python3

"""
WEEELAB - Log management module for garbaging paper sign sheet.
Author: WeeeOpen Team
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
from datetime import *
import sys

__version__ = "2.3"
__author__ = "WEEE Open team"

EXECNAME = os.path.basename(__file__)  # name of this file
debuggingState = False  # Disable owncloud uploads during debug sessions
user_list = []  # list of users in users file (

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


class User:
    def __init__(self, name='', surname='', serial='', level=0, telegramid='',
                 nickname=''):
        if isinstance(name, dict):
            self.name = name['name']
            self.surname = name['surname']
            self.serial = name['serial']
            self.level = name['level']
            self.telegramID = name['telegramID']
            self.nickname = name['nickname']
        else:
            self.name = str(name)
            self.surname = str(surname)
            self.serial = str(serial)
            self.level = int(level)
            self.telegramID = str(telegramid)
            self.nickname = str(nickname)

    def __str__(self):
        return self.name + ' ' + self.surname

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def isthis(self, username):
        if username == '':
            return False
        username = username.lower()
        if '.' in username:
            return self.name.lower() == username.split('.')[0] and \
                   self.surname.lower() == username.split('.')[1]
        elif ' ' in username:
            return self.name.lower() == username.split()[0] and \
                   self.surname.lower() == username.split()[1]
        else:
            return username in (self.serial, self.telegramID,
                                self.nickname.lower())


def get_user(username):
    """
    Check if an username exists in users list file.
    :param username: string
    :return: 'Name Surname' -> of that username
             '' -> username don't exist
    """
    for user in user_list:
        if user.isthis(username):
            return user
    raise NameError('')


def td2str(tmdelta):
    """
    Convert timedelta in a formatted string
    :param tmdelta: timedelta
    :return: string -> 'hh:mm'
    """
    seconds = tmdelta.total_seconds()
    hh = str(int(seconds // 3600)).zfill(2)
    mm = str(int((seconds % 3600) // 60)).zfill(2)
    return hh + ':' + mm


class LogRow:
    """
    LogRow -  row of log.dat
    '%Y-%m-%d %H:%M - %H:%M - username - workdone'

    timein : <datetime> datetime.now()
    timework : <timedelta> = 'INLAB'
    username : <string> = '__user__'
    workdone : <string> = ''
    """
    sep = ' - '
    mask_datetime = '%Y-%m-%d %H:%M'
    presence = 'INLAB'
    len_wd = 128

    def __init__(self, row=''):
        if row == '':
            self.timein = datetime.now()
            self.timework = self.presence
            self.user = '__user__'
            self.workdone = ''
        else:
            row_args = [arg.strip() for arg in row.split(self.sep)]
            self.timein = datetime.strptime(row_args[0],
                                            self.mask_datetime)
            td = row_args[1]
            if td == self.presence:
                self.timework = self.presence
            else:
                self.timework = timedelta(hours=int(td.split(':')[0]),
                                          minutes=int(td.split(':')[1]))
            self.user = get_user(row_args[2])
            self.workdone = self.sep.join(row_args[3:])

    def __str__(self):
        if self.inlab():
            tmwork = self.presence
        else:
            tmwork = td2str(self.timework)
        return self.sep.join((self.timein.strftime(self.mask_datetime),
                              tmwork, str(self.user), self.workdone)) + '\n'

    def inlab(self, user=''):
        """
        Return True if <username> is logged in else False
        :param user: User
        :return: bool
        """
        if user:
            return (self.timework == self.presence) and (
                    self.user == user)
        else:
            return self.timework == self.presence

    def logout(self, workdone):
        """
        Set <time_work> and <workdone>
        :param workdone: string
        :return: True -> logout success
                 False -> Logout unsuccess
        """
        if self.inlab() and len(workdone) < self.len_wd:
            self.timework = datetime.now() - self.timein
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


# check if the passed date is in the right format
def checkDate(input):  # TODO check_date
    date = input.split("/")

    if len(date[0]) != 2 or len(date[1]) != 2 or len(date[2]) != 4:
        print("date format error")
        secure_exit(2)
    return input


def checkHour(input):  # TODO check_hour
    hour = input.split(":")
    if len(hour) != 2:
        print("wrong hour format")
        secure_exit(2)
    return input


def get_log():
    """
    Return a list of all line content in log file
    :return: list -> All log file
    """
    with open(LOG_PATH) as log_file:
        log_list = log_file.readlines()
    return log_list


def get_inlab():
    """
    Get the list of logged in users
    :return: list of User -> all users in lab
             [] -> nobody is in lab
    """
    users_in_lab = []
    for line in get_log():
        lr = LogRow(line)
        if lr.inlab():
            users_in_lab.append(lr.user)
    return users_in_lab


def is_inlab(user):
    """
    Check if user is in lab
    :param user: User
    :return: True -> user is in lab
             False -> user isn't in lab
    """
    for user_inlab in get_inlab():
        if user_inlab == user:
            return True
    return False


def login(user):
    """
    Write a new LogRow in log file
    :param user: User
    :return: 0 -> Login success
             1 -> user is already in lab
    """
    if is_inlab(user):
        return 1
    else:
        lg = LogRow()
        lg.user = user
        with open(LOG_PATH, 'a') as log_file:
            log_file.write(str(lg))
        if not debuggingState:  # Send to ownCloud folder
            os.system("cp " + LOG_PATH + " " + BACKUP_PATH + "log.txt")
        return 0


def logout(user, workdone):
    """
    Edit a LogRow and rewrite the log file
    :param user: User
    :param workdone: string
    :return: 0 -> Logout success
             1 -> user isn't in lab
             2 -> Workdone too long
    """
    workdone = str(workdone)
    if len(workdone) > LogRow.len_wd:
        return 2

    found = False
    log_list = []
    # si salva tutto il file nella lista, se trova la voce che contiene
    # INLAB e username del logout modifica quella stringa
    for line in get_log():
        lr = LogRow(line)
        if lr.inlab(user):
            found = True
            lr.logout(workdone)
        log_list.append(str(lr))  # Store everything in the list

    if found:
        # Writing everything to log file
        with open(LOG_PATH, 'w') as log_file:
            for line in log_list:
                log_file.write(line)
        if not debuggingState:
            # Send to ownCloud folder
            os.system("cp " + LOG_PATH + " " + BACKUP_PATH + "log.txt")
        return 0
    else:
        return 1


# logout by passing manually date and time
def manualLogout():  # TODO manual_logout review
    tmpUsr = input("ADMIN--> insert username: ")
    username = get_user(tmpUsr)

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

    logout(username, workdone)


def stat(user):
    """
    Calculates all time spent in lab for that user
    :param user: User
    :return: timedelta -> total of time spent in lab
    """
    total_timework = timedelta()
    for line in get_log():
        lg = LogRow(line)
        if (lg.user == user) and not lg.inlab():
            total_timework += lg.timework
    return total_timework


def top():
    """
    Return stat() for all users with minutes in lab
    :return: list of (timedelta, User) ->
    """
    stat_list = []
    for user in user_list:
        t_tw = stat(user)
        if t_tw > timedelta():
            stat_list.append((stat(user), user))
    stat_list.sort(reverse=True)
    return stat_list


# Repetitive print...
def __p_host(string=''):
    print(HOSTNAME + ': ' + string)


def __p_usage(string=''):
    print('usage: ' + EXECNAME + ' ' + string)


def __p_error(string=''):
    print('error: ' + string)


def cmd_help(cmd=''):
    if cmd == "login":
        __p_usage("login <username>")
        __p_host("Username format is 'name.surname' or 'XXXXXX'")
        print("                where XXXXXX is your serial number.")
        print("                You can even use a nickname if defined.")
        secure_exit()

    elif cmd == "logout":
        __p_usage("logout <username>")
        __p_host("Username format is 'name.surname' or 'XXXXXX'")
        print("                where XXXXXX is your serial number.")
        print("                You can even use a nickname if defined.")
        secure_exit()

    elif cmd == "show":
        __p_usage("show <option>")
        __p_host("available options:")
        print("               log : Show log file.")
        print("             inlab : Show a list of students in lab now.")
        secure_exit()

    elif cmd == "stat":
        __p_usage("stat <username>")
        __p_host("Show time spend in lab for <username>.")

    elif cmd == "top":
        __p_usage("top <list_length>")
        __p_host("Show Hall of Fame.")

    else:
        print("WEEELAB v" + __version__ +
              " - Log management module for garbaging paper sign sheet.")
        print("Author: WeeeOpen Team")
        print("Copyright (C) 2017 WeeeOpen - Politecnico di Torino")
        print("This program comes with ABSOLUTELY NO WARRANTY.")
        print("Since this is a free software, you are welcome")
        print("to redistribute it under the terms of the GNU GPLv3.\n")
        print("  Available commands:")
        print("    login  <username> : Sign access to the lab.")
        print("    logout <username> : Sign quit from the lab.")
        print("    show   <option>   : Retrieve informations.")
        print("    stat   <username> : Compute stats for a user.")
        print("    top <int> : Show a list of top <int> members.")
        secure_exit()


def main(args):
    if len(args) < 2:
        __p_usage("<command> <arguments>")
        secure_exit()
    command = args[1]

    # Add commands here
    if command == "help":
        if len(args) < 3:
            cmd_help()
        elif len(args) >= 3:
            cmd_help(args[2])

    elif command == "login":
        if len(args) != 3:
            __p_usage("login <username>")
            secure_exit()
        else:
            try:
                user = get_user(args[2])
                result = login(user)
                if result == 0:
                    __p_host("Login successful! Hello " + str(user) + "!")
                elif result == 1:
                    __p_host(str(user) + ", you're already logged in.")
            except NameError:  # if user not found
                __p_error("Username not recognized.")
                __p_host("Maybe you misspelled it or you're an intruder.")

    elif command == "logout":
        if len(args) != 3:
            __p_usage("logout <username>")
            secure_exit()
        else:
            try:
                user = get_user(args[2])
                if is_inlab(user):
                    if len(args) == 4:
                        workdone = args[3]
                        logout(user, workdone)
                    else:
                        try:
                            workdone = input(HOSTNAME + ": What have you done?\n")
                            while len(workdone) > LogRow.len_wd:
                                __p_host("I didn't ask the story of your life!")
                                workdone = input(
                                    HOSTNAME + ": What have you done? [BRIEFLY]\n")
                            logout(user, workdone)
                            __p_host("Logout successful! Bye " + str(user) + "!")
                        except KeyboardInterrupt:
                            __p_host("Logout fail! Sorry " + str(user) + "!")
                    else:
                        __p_host(str(user) + " is not in lab!")
            except NameError:  # if user not found
                __p_error("Username not recognized.")
                __p_host("Maybe you misspelled it or you're an intruder.")

    elif command == "show":
        if len(args) != 3:
            __p_usage(EXECNAME + " show <option>")
            print("  available options:")
            print("      log : Print log file to stdout.")
            print("    inlab : View a list of students in lab now.")
            secure_exit()
        else:
            if args[2] == "log":
                __p_host("Reading log file...\n")
                print(''.join(get_log()))

            elif args[2] == "inlab":
                users_inlab = get_inlab()
                count = len(users_inlab)
                __p_host("Reading log file...\n")
                for user in users_inlab:
                    print("> " + str(user))
                if count == 0:
                    __p_host("Nobody is in lab right now.")
                elif count == 1:
                    __p_host("There is one student in lab right now.")
                else:
                    __p_host("There are {c} students in lab right now.".format(
                        c=count))

            elif args[2] == "help":
                cmd_help()

            else:
                print("error: option <" + args[2] + "> is not defined.")

    elif command == "stat":
        if len(args) != 3:
            __p_usage("stat <username>")
            secure_exit()
        else:
            try:
                user = get_user(args[2])
                __p_host("Computing stats...\n")
                print(datetime.now().strftime("In %B %Y :"))
                print('> ' + td2str(stat(user)) + ' - ' + str(user))
            except NameError:  # if user not found
                __p_error("Username not recognized.")
                __p_host("Maybe you misspelled it or you're an intruder.")

    elif command == "top":
        if len(args) == 3:
            if not args[2].isdigit:
                __p_usage("top <list_length>")
                secure_exit()
            else:
                __p_host("Computing Hall of Fame...\n")
                print(datetime.now().strftime("In %B %Y :"))
                print('pos) hh:mm - Name Surname')
                count = 0
                for item in top():
                    count += 1
                    print('{} ) {} - {}'.format(str(count).zfill(2),
                                                td2str(item[0]), str(item[1])))
                    if count >= int(args[2]):
                        break
        else:
            __p_host("Computing Hall of Fame...\n")
            print(datetime.now().strftime("In %B %Y :"))
            print('pos) hh:mm - Name Surname')
            count = 0
            for item in top():
                count += 1
                print('{} ) {} - {}'.format(str(count).zfill(2),
                                            td2str(item[0]), str(item[1])))
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
    # Check if users list file exists.
    if not os.path.isfile(USERS_PATH):
        __p_error("Users file not found.")
        secure_exit(2)
    # Check USERS_PATH integrity
    try:
        with open(USERS_PATH) as user_file:
            users_dict = json.load(user_file)
            for user in users_dict['users']:
                user_list.append(User(user))
    except:
        __p_error("User file have an errors")
        secure_exit(2)
    # Check if LOG_PATH exist, if no make it
    if not os.path.isfile(LOG_PATH):
        with open(LOG_PATH, 'x'):
            __p_host("New log file was created.")
    # check integrity of LOG_PATH
    counter = 0
    try:
        for line in get_log():
            counter += 1
            LogRow(line)
    except:
        __p_error("Log file have an error at line " + str(counter))
    # se è un nuovo mese rinomina log.dat in log%Y-%m.dat e ne crea una copia
    if len(get_log()):
        last_date = LogRow(get_log()[-1]).timein
        last_month, last_year = last_date.month, last_date.year
        curr_date = datetime.now()
        curr_month, curr_year = curr_date.month, curr_date.year
        if (curr_month > last_month and curr_year == last_year) or (
                curr_year > last_year):
            __p_host("Backing up log file...")
            file_ext = os.path.splitext(LOG_PATH)[1]
            new_path = LOG_PATH[:-len(file_ext)] + last_date.strftime(
                '%Y-%m') + '.' + file_ext
            os.rename(LOG_PATH, new_path)
            if not debuggingState:
                # Send to ownCloud folder
                os.system("cp " + new_path + " " + BACKUP_PATH +
                          "log" + last_date.strftime('%Y-%m') + ".txt")
            if not os.path.isfile(LOG_PATH):
                with open(LOG_PATH, 'x'):
                    __p_host("New log file was created.")


sanity_check()
if __name__ == '__main__':
    main(sys.argv)
