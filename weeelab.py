#!/usr/bin/env python3

"""
WEEELAB - Log management module for garbaging paper sign sheet.
Author: Hyd3L

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
import sys
import json
# Allows using backspace and arrow keys in input
import readline
from socket import gethostname
from getpass import getuser
from datetime import datetime

COLOR_RED = "\033[1;31m"
COLOR_STANDARD = "\033[;7m"
COLOR_NATIVE = "\033[m"

VERSION = "1.4.1"
EXECNAME = __file__.split('/')[-1]

UID = os.getuid()
HOSTNAME = gethostname()
HOSTUSER = getuser()
LOG_PATH = "/home/" + HOSTUSER + "/.local/share/" + EXECNAME + "/log.txt"
USERS_PATH = "/home/" + HOSTUSER + "/ownCloud/Weeelab/users.json"
BACKUP_PATH = "/home/" + HOSTUSER + "/ownCloud/weeeopen/" + EXECNAME.capitalize() + "/"

# Disable owncloud uploads during debug sessions
debuggingState = False


# terminate the program being sure about undoing some changes like cli color
def secure_exit(return_value=0):
    sys.stdout.write(COLOR_NATIVE)
    sys.exit(return_value)


# root execution check
if UID == 0:
    print("Error: can't execute " + EXECNAME + " as root.")
    secure_exit(42)


# TODO: use argparse and enter the 21st century
def print_help(for_what):
    if for_what == "login":
        print("usage: " + EXECNAME + " login <username>")
        print(HOSTNAME + ": Username format is 'first.last' or 'XXXXXX'")
        print("                where XXXXXX is your serial number.")
        print("                You can even use an alias if defined.")
        secure_exit()

    elif for_what == "logout":
        print("usage: " + EXECNAME + " logout <username>")
        print(HOSTNAME + ": Username format is 'first.last'")
        print("                where XXXXXX is your serial number.")
        print("                You can even use an alias if defined.")
        secure_exit()

    elif for_what == "show":
        print("usage: " + EXECNAME + " show <option>")
        print("  available options:")
        print("      log : Print log file to stdout.")
        print("    inlab : View a list of students in lab now.")
        secure_exit()

    elif for_what == "stat":
        print("usage: " + EXECNAME + " stat <username>")
        print(HOSTNAME + ": If you want to view stats for everybody,")
        print("                use \"" + EXECNAME + " stat all\"")

    elif for_what == "top":
        print("usage: " + EXECNAME + " top <list_length>")

    else:
        print("WEEELAB v" + VERSION + " - Log management module for garbaging paper sign sheet.")
        print("Author: Stefano Enrico Mendola (aka Hyd3L, STE col teschio)")
        print("Copyright (C) 2017 WeeeOpen - Politecnico di Torino")
        print("This program comes with ABSOLUTELY NO WARRANTY.")
        print("Since this is a free software, you are welcome")
        print("to redistribute it under the terms of the GNU GPLv3.\n")
        print("  Available commands:")
        print("    login  <username> : Sign access to the lab.")
        print("    logout <username> : Sign quit from the lab.")
        print("    show   <option>   : Retrieve informations.")
        print("    stat   <username> : Compute stats for a user or for all users.")
        print("    top <list_length> : Show a list of top <list_length> members.")
        secure_exit()


# Check if log file exists.
def check_log_file():
    if os.path.isfile(LOG_PATH) is False:
        print("error: Log file not found in {}.".format(LOG_PATH1))
        secure_exit(1)


# Check if users list file exists.
def check_users_file():
    if os.path.isfile(USERS_PATH) is False:
        print("error: Users list not found.")
        secure_exit(2)


# check if the passed date is in the right format
def check_date(input_date):
    date = input_date.split("/")

    '''
    # debug only
    print str(len(date[0]))
    print str(len(date[1]))
    print str(len(date[2]))
    '''

    if len(date[0]) != 2 or len(date[1]) != 2 or len(date[2]) != 4:
        print("date format error")
        secure_exit(2)
    return input_date


def check_hour(input_hour):
    hour = input_hour.split(":")
    if len(hour) != 2:
        print("wrong hour format")
        secure_exit(2)
    return input_hour


# Check if an username exists in users list file.
def check_member(username):
    check_users_file()
    found = False
    users_file = open(USERS_PATH)
    users_list = json.loads(users_file.read())
    users_file.close()

    for u in users_list['users']:
        if username == str(u['serial']) or username == str(u['nickname']):
            found = True
            username = str(u['name']).lower() + '.' + str(u['surname']).lower()
            break

    if not found:
        print("error: Username not recognized.")
        print(HOSTNAME + ": Maybe you misspelled it or you're an intruder.")
        secure_exit(2)
    return username

# Check if user is already logged in.
def is_logged_in(username):
    logged = False
    log_file = open(LOG_PATH, "r")
    for line in log_file:
        if ("INLAB" in line) and (username in line):
            logged = True
            break
    log_file.close()
    return logged


# TODO: this is bad practice and doesn't make any sense, replace by reading name and surname from JSON...
def name_extr(username):
    first_name = username.split('.')[0].capitalize()
    last_name = username.split('.')[1].capitalize()
    return first_name + " " + last_name


# Check if inputFile is empty.
def is_empty(input_file):
    if str(input_file.read())[:1] == "":
        input_file.close()
        return True
    else:
        input_file.seek(0)
        return False


def create_backup_if_necessary():
    log_file = open(LOG_PATH, "r")
    if is_empty(log_file) is False:
        last_line = str(log_file.read())[4:11]
        log_file.close()

        curr_month = int(datetime.now().strftime("%m"))
        curr_year = int(datetime.now().strftime("%Y"))
        last_month = int(datetime.now().strptime(last_line, "%m/%Y").strftime("%m"))
        last_year = int(datetime.now().strptime(last_line, "%m/%Y").strftime("%Y"))

        if (curr_month > last_month) or (curr_year > last_year):
            print(HOSTNAME + ": Backing up log file... ")
            new_path = LOG_PATH[:len(LOG_PATH) - 4] + str(last_year) + str(last_month).zfill(2) + ".dat"
            os.rename(LOG_PATH, new_path)
            if not debugging_state:
                # Send to ownCloud folder
                os.system(
                    "cp " + new_path + " " + BACKUP_PATH + "log" + str(last_year) + str(last_month).zfill(2) + ".txt")
            print("Done!")
            log_file = open(LOG_PATH, "w")
            log_file.close()
            print(HOSTNAME + ": New log file was created.")


def login(username):
    check_log_file()
    create_backup_if_necessary()
    username = check_member(username)
    curr_time = datetime.now().strftime("%d/%m/%Y %H:%M")
    login_string = "[" + curr_time + "] " + "[----------------] [INLAB] " + "<" + username + ">" + "\n"

    if is_logged_in(username):
        print(HOSTNAME + ": " + name_extr(username) + ", you're already logged in.")
    else:
        log_file = open(LOG_PATH, "a")
        log_file.write(login_string)
        log_file.close()
        if not debugging_state:
            # Send to ownCloud folder
            os.system("cp " + LOG_PATH + " " + BACKUP_PATH + "log.txt")
        print(HOSTNAME + ": Login successful! Hello " + name_extr(username) + "!")


# Returns the time spent in lab formatted as HH:MM
def work_time(timein, timeout):
    li = (int(timein[:2]) * 60) + int(timein[3:5])
    lo = (int(timeout[:2]) * 60) + int(timeout[3:5])
    hours = (lo - li) / 60
    minutes = (lo - li) % 60
    return str(hours).zfill(2) + ":" + str(minutes).zfill(2)


def write_logout(username, curr_time, workdone):
    check_log_file()

    found = False

    log_list = []
    log_file = open(LOG_PATH, "r")
    # si salva tutto il file nella lista,
    # se trova la voce che contiene INLAB e username del logout modifica quella stringa
    for line in log_file:
        if ("INLAB" in line) and (username in line):
            found = True
            login_time = line[12:17]
            logout_time = curr_time[11:17]
            line = line.replace("----------------", curr_time)
            line = line.replace("INLAB", work_time(login_time, logout_time))
            line = line.replace("\n", "")

            line = line + " :: " + workdone + "\n"
        log_list.append(line)  # Store everything in the list
    log_file.close()

    if found:
        # Writing everything to log file
        log_file = open(LOG_PATH, "w")
        for line in log_list:
            log_file.write(line)
        log_file.close()
        if not debugging_state:
            # Send to ownCloud folder
            os.system("cp " + LOG_PATH + " " + BACKUP_PATH + "log.txt")
        print(HOSTNAME + ": Logout successful! Bye " + name_extr(username) + "!")
    else:
        print(HOSTNAME + ": " + name_extr(username) + " is not in lab!")


def logout(username):
    check_log_file()
    username = check_member(username)
    #   passing it by value is better
    curr_time = datetime.now().strftime("%d/%m/%Y %H:%M")
    workdone = input(HOSTNAME + ": What have you done?\n:: ")
    while len(workdone) > 128:
        print(HOSTNAME + ": I didn't ask you the story of your life!")
        workdone = input(HOSTNAME + ": What have you done? [BRIEFLY]\n>> ")
    write_logout(username, curr_time, workdone)


# logout by passing manually date and time
def manual_logout():
    check_log_file()
    tmp_usr = input("ADMIN--> insert username: ")
    username = check_member(tmp_usr)

    tmp_date = input("ADMIN--> insert date (gg/mm/aaaa): ")
    date = check_date(tmp_date)

    tmp_h = input("ADMIN--> insert time (hh:mm): ")
    hour = check_hour(tmp_h)

    curr_time = date + " " + hour

    workdone = input(HOSTNAME + ": What have you done?\n:: ")
    while len(workdone) > 128:
        print(HOSTNAME + ": I didn't ask you the story of your life!")
        workdone = input(HOSTNAME + ": What have you done? [BRIEFLY]\n>> ")

    print("ADMIN--> you will update the log file with ")
    print("            " + username + " " + curr_time)
    answer = input("ADMIN--> are you sure? (y/n)")
    if answer != "y":
        secure_exit()

    write_logout(username, curr_time, workdone)


def show(option):
    check_log_file()

    if option == "log":
        print(HOSTNAME + ": Reading log file...\n")
        log_file = open(LOG_PATH, "r")
        for line in log_file:
            print(line)
        log_file.close()

    elif option == "inlab":
        count = 0
        curr_day = datetime.now().strftime("%d/%m/%Y")
        print(HOSTNAME + ": Reading log file...\n")
        log_file = open(LOG_PATH, "r")
        for line in log_file:
            if ("INLAB" in line) and (curr_day in line):
                count += 1
                print("> " + name_extr(line[47:line.rfind(">")]))
        log_file.close()

        if count == 0:
            print(HOSTNAME + ": Nobody is in lab right now.")
        elif count == 1:
            print(HOSTNAME + ": There is one student in lab right now.")
        else:
            print(HOSTNAME + ": There are {c} students in lab right now.".format(c=count))

    elif option == "help":
        print_help("default")

    else:
        print("error: option " + option + " is not defined.")


# Returns total work time in minutes
def tot_work_time(username):
    check_log_file()
    time_spent = 0
    log_file = open(LOG_PATH, "r")
    for line in log_file:
        if (username in line) and not ("INLAB" in line):
            time_spent += ((int(line[39:41]) * 60) + int(line[42:44]))
    log_file.close()
    return time_spent


# Convert minutes in a formatted string
def time_conv(minutes):
    return str(minutes / 60) + "h " + str(minutes % 60) + "m"


def stat(username):
    print(HOSTNAME + ": Computing stats...\n")
    curr_month = datetime.now().strftime(" [%B %Y]")

    # Compute stats for all users (Extremely stupid algorithm, but works fine)
    if username == "all":
        check_users_file()
        users_file = open(USERS_PATH, "r")
        for line in users_file:
            # for some reasons line.split(" ") gave problems, so it's best to use line.split()
            curr_user = line.split()[0]
            print("[+]     Name: " + name_extr(curr_user))
            print("[+] WorkTime: " + time_conv(tot_work_time(curr_user)) + curr_month + "\n")
        users_file.close()

    else:
        username = check_member(username)
        print("[+]     Name: " + name_extr(username))
        print("[+] WorkTime: " + time_conv(tot_work_time(username)) + curr_month)


# Print users list ordered by most active first.
def top(length):
    check_users_file()
    users_list = [(int, str)]
    users_file = open(USERS_PATH, "r")

    # Loading usernames from file
    for line in users_file:
        users_list.append((0, line.split(" ")[0].replace("\n", "")))
    users_file.close()
    users_list.remove((int, str))

    # Computing total work time for each member
    for i in range(0, len(users_list)):
        user = users_list[i]
        user = (tot_work_time(user[1]),) + user[1:]
        users_list[i] = user
    users_list.sort(reverse=True)

    print(HOSTNAME + ": Hall of Fame\n")
    count = 1
    for i in range(0, length):
        if len(users_list) <= i:
            break
        print("[" + str(count).zfill(2) + "] " + name_extr(users_list[i][1]))
        count += 1


def main(args):
    if len(args) < 2:
        print("usage: " + EXECNAME + " <command> <arguments>")
        secure_exit()
    command = args[1]

    # Add commands here
    if command == "help":
        if len(args) < 3:
            print_help("default")
        elif len(args) >= 3:
            print_help(args[2])

    elif command == "login":
        if len(args) != 3:
            print("usage: " + EXECNAME + " login <username>")
            secure_exit()
        else:
            login(args[2])

    elif command == "logout":
        if len(args) != 3:
            print("usage: " + EXECNAME + " logout <username>")
            secure_exit()
        else:
            username = check_member(args[2])
            curr_time = datetime.now().strftime("%d/%m/%Y %H:%M")
            workdone = input(HOSTNAME + ": What have you done?\n:: ")
            while len(workdone) > 128:
                print(HOSTNAME + ": I didn't ask you the story of your life!")
                workdone = input(HOSTNAME + ": What have you done? [BRIEFLY]\n>> ")
            write_logout(username, curr_time, workdone)

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
            print("usage: " + EXECNAME + " admin <logout>")
            secure_exit()
        else:
            manual_logout()
            sys.stdout.write(COLOR_NATIVE)

    else:
        print("error: Invalid command detected -> " + args[1])
        print(HOSTNAME + ": Try with \"" + EXECNAME + " help\"")


if __name__ == '__main__':
    main(sys.argv)
