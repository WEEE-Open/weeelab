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
import argparse
# For the copyright string in --help
from argparse import RawDescriptionHelpFormatter
from shutil import copy2
# Allows using backspace and arrow keys in input
# noinspection PyUnresolvedReferences
import readline
from socket import gethostname
from getpass import getuser
from datetime import datetime

COLOR_RED = "\033[1;31m"
COLOR_NATIVE = "\033[m"

VERSION = "2.0"
PROGRAM_NAME = __file__.split('/')[-1]

HOST_NAME = gethostname()
HOST_USER = getuser()
DEBUG_MODE = False  # Don't set it here, use -d when running
LOG_FILENAME = "/home/" + HOST_USER + "/.local/share/" + PROGRAM_NAME + "/log.txt"
USERS_PATH = "/home/" + HOST_USER + "/ownCloud/Weeelab/users.json"
BACKUP_PATH = "/home/" + HOST_USER + "/ownCloud/weeeopen/" + PROGRAM_NAME.capitalize() + "/"


def secure_exit(return_value=0):
	"""
	Terminate the program being sure about undoing some changes like CLI color

	:param return_value: return this to the caller
	"""
	sys.stdout.write(COLOR_NATIVE)
	sys.exit(return_value)


def check_date(input_date: str) -> bool:
	"""
	Check if date is in the right format

	:param input_date: Some representation of a date
	:return: True if valid, false otherwise
	"""
	date = input_date.split("/")

	if len(date[0]) != 2 or len(date[1]) != 2 or len(date[2]) != 4:
		print("date format error")
		return False
	return True


def check_hour(input_hour: str) -> bool:
	"""
	Check if hour is in the right format

	:param input_hour:
	:return:
	"""
	hour = input_hour.split(":")
	if len(hour) != 2:
		print("wrong hour format")
		return False
	return True


def get_normalized_username(username: str, users: map) -> str:
	"""
	Normalize user name using the

	:param users: JSON file as map
	:param username: Supplied username, to search and normalize
	:return: normalized username
	"""
	found = False
	username_lower = username.lower()

	# Map lookup should be pretty fast, so let's optimize for the easy case...
	if username_lower in users:
		return username_lower

	# Note that an username could contain uppercase characters, so we can't skip checking that...
	for key in users:
		entry = users[key]

		if username_lower == str(entry['username']).lower():
			found = True
			username = key
			break

		if 'serial' in entry:
			if username_lower == str(entry['serial']).lower():
				found = True
				username = key
				break

		if 'nicknames' in entry:
			for nick in entry['nicknames']:
				if username_lower == nick.lower():
					# Break inner loop only
					found = True
					break
			if found:
				# Break outer loop
				username = key
				break

	if not found:
		print(HOST_NAME + ": Username not recognized. Maybe you misspelled it or you're an intruder.")
		secure_exit(2)
	return username


def is_logged_in(username: str) -> bool:
	"""
	Check if user is already logged in.

	:param username: normalized username
	:return:
	"""
	logged = False
	log_file = open(LOG_FILENAME, "r")
	for line in log_file:
		if ("INLAB" in line) and (username in line):
			logged = True
			break
	log_file.close()
	return logged


def name_pretty_print(entry: dict) -> str:
	"""
	Pretty-print name from users file

	:param entry: JSON file entry as dict
	:return: Name Surname
	"""
	return entry['name'] + " " + entry['surname']


def is_empty(input_file) -> bool:
	"""
	Check if inputFile is empty.

	:param input_file:
	:return:
	"""
	if str(input_file.read())[:1] == "":
		input_file.close()
		return True
	else:
		input_file.seek(0)
		return False


def ensure_log_file():
	if os.path.exists(LOG_FILENAME) is False:
		if os.path.isdir(os.path.dirname(LOG_FILENAME)):
			print(HOST_NAME + ": creating empty log.txt")
			open(LOG_FILENAME, "a").close()
		else:
			print(HOST_NAME + ": cannot find directory {}".format(os.path.dirname(LOG_FILENAME)))
			secure_exit(1)


def get_users_file() -> map:
	"""
	Get users from the users file.
	"""
	try:
		users_file = open(USERS_PATH)
	except FileNotFoundError:
		print(HOST_NAME + ": users list not found in {}".format(USERS_PATH))
		secure_exit(2)
		return {}  # Just prevents PyCharm from complaining

	try:
		users_list = json.loads(users_file.read())
	except ValueError:
		print(HOST_NAME + ": cannot parse users list {}, syntax error".format(USERS_PATH))
		secure_exit(2)
		return {}  # Just prevents PyCharm from complaining
	finally:
		users_file.close()

	users_map = {}
	for entry in users_list['users']:
		if 'username' not in entry:
			print(HOST_NAME + ": error reading JSON file, missing username for entry:\n{}".format(str(entry)))
			secure_exit(2)
		users_map[entry['username']] = entry

	return users_map


def store_log_to(filename, destination):
	"""
	Copy a log file (or anything, really) to a directory, if DEBUG_MODE is False

	:param filename: Path to source file
	:param destination: Path to destination file or directory
	"""
	if DEBUG_MODE is True:
		print(HOST_NAME + ": DEBUG_MODE, skipped copying {} to {}".format(os.path.basename(filename), destination))
	else:
		copy2(filename, destination)


def create_backup_if_necessary():
	# Open master log file
	log_file = open(LOG_FILENAME, "r")
	if is_empty(log_file) is False:
		last_month_year = str(log_file.read())[4:11]

		curr_month = int(datetime.now().strftime("%m"))
		curr_year = int(datetime.now().strftime("%Y"))
		last_date = datetime.strptime(last_month_year, "%m/%Y")
		last_month = int(last_date.strftime("%m"))
		last_year = int(last_date.strftime("%Y"))

		# If the inexorable passage of time has been perceived by this program, too...
		if (curr_month > last_month) or (curr_year > last_year):
			stored_log_filename = LOG_FILENAME.rsplit('.', 1)[0] + last_date.strftime("%Y%m") + ".txt"
			print(HOST_NAME + ": Backing up log file to {}".format(os.path.basename(stored_log_filename)))
			os.rename(LOG_FILENAME, stored_log_filename)
			store_log_to(stored_log_filename, BACKUP_PATH)
			print(HOST_NAME + ": Done!")

			open(LOG_FILENAME, "a").close()
			print(HOST_NAME + ": New log file was created.")
	log_file.close()


def login(username: str, users: map):
	"""
	Log in. Add the line in the file. Do it.

	:param username: User-supplied username
	:param users: Users JSON as a map
	"""
	username = get_normalized_username(username, users)

	if is_logged_in(username):
		print(HOST_NAME + ": {}, you're already logged in.".format(name_pretty_print(users[username])))
	else:
		curr_time = datetime.now().strftime("%d/%m/%Y %H:%M")
		login_string = "[{date}] [----------------] [INLAB] <{name}>\n".format(date=curr_time, name=username)
		log_file = open(LOG_FILENAME, "a")
		log_file.write(login_string)
		log_file.close()

		store_log_to(LOG_FILENAME, BACKUP_PATH)

		print(HOST_NAME + ": Login successful! Hello {}!".format(name_pretty_print(users[username])))


def logout(username: str, users: map):
	"""
	Log out.

	:param username: User-supplied username
	:param users: Users JSON as a map
	"""
	username = get_normalized_username(username, users)
	if not is_logged_in(username):
		print(HOST_NAME + ": you aren't in lab! Did you forget to log in?")
		secure_exit(3)

	curr_time = datetime.now().strftime("%d/%m/%Y %H:%M")
	workdone = ask_work_done()

	if write_logout(username, curr_time, workdone):
		print(HOST_NAME + ": Logout successful! Bye {}!".format(name_pretty_print(users[username])))
	else:
		print(HOST_NAME + ": Logout failed")
		secure_exit(3)


def ask_work_done():
	try:
		workdone = input(HOST_NAME + ": What have you done?\n:: ")
		while len(workdone) > 128:
			print(HOST_NAME + ": I didn't ask you the story of your life!")
			workdone = input(HOST_NAME + ": What have you done? [BRIEFLY]\n:: ")
	except KeyboardInterrupt:
		print(HOST_NAME + ": Logout cancelled by keboard interrupt")
		secure_exit(5)
		return None  # Just prevents PyCharm from complaining
	return workdone


def work_time(timein, timeout) -> str:
	"""
	Returns the time spent in lab formatted as HH:MM

	TODO: something more robust than manual time math...
	"""
	li = (int(timein[:2]) * 60) + int(timein[3:5])
	lo = (int(timeout[:2]) * 60) + int(timeout[3:5])
	hours = int((lo - li) / 60)
	minutes = int((lo - li) % 60)
	return str(hours).zfill(2) + ":" + str(minutes).zfill(2)


def write_logout(username, curr_time, workdone) -> bool:
	"""
	I don't even want to know. This thing works, it's ok, don't touch it
	"""
	found = False

	log_list = []
	log_file = open(LOG_FILENAME, "r")
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
		log_file = open(LOG_FILENAME, "w")
		for line in log_list:
			log_file.write(line)
		log_file.close()

		store_log_to(LOG_FILENAME, BACKUP_PATH)

		return True
	else:
		return False


# logout by passing manually date and time
def manual_logout(users: map):
	sys.stdout.write(COLOR_RED)
	tmp_usr = input("ADMIN--> insert username: ")
	username = get_normalized_username(tmp_usr, users)

	date = input("ADMIN--> insert date (gg/mm/aaaa): ")
	if not check_date(date):
		secure_exit(4)

	hour = input("ADMIN--> insert time (hh:mm): ")
	if not check_hour(hour):
		secure_exit(4)

	curr_time = date + " " + hour

	workdone = ask_work_done()

	print("ADMIN--> you will update the log file with ")
	print("            " + username + " " + curr_time)
	answer = input("ADMIN--> are you sure? (y/n)")
	if answer != "y":
		secure_exit(4)

	if write_logout(username, curr_time, workdone):
		print("ADMIN--> Update succeeded")
	else:
		print("ADMIN--> Update failed (not logged in?)")


def logfile():
	print(HOST_NAME + ": Reading log file...\n")
	log_file = open(LOG_FILENAME, "r")
	for line in log_file:
		print(line)
	log_file.close()


def inlab(users: map):
	count = 0
	curr_day = datetime.now().strftime("%d/%m/%Y")
	print(HOST_NAME + ": Reading log file...\n")
	log_file = open(LOG_FILENAME, "r")
	for line in log_file:
		if ("INLAB" in line) and (curr_day in line):
			count += 1
			username = line[47:line.rfind(">")]
			print("> " + name_pretty_print(users[username]))
	log_file.close()

	if count == 0:
		print(HOST_NAME + ": Nobody is in lab right now.")
	elif count == 1:
		print(HOST_NAME + ": There is one student in lab right now.")
	else:
		print(HOST_NAME + ": There are {c} students in lab right now.".format(c=count))


# Returns total work time in minutes
def tot_work_time(username):
	time_spent = 0
	log_file = open(LOG_FILENAME, "r")
	for line in log_file:
		if (username in line) and not ("INLAB" in line):
			time_spent += ((int(line[39:41]) * 60) + int(line[42:44]))
	log_file.close()
	return time_spent


def stat(users: map, username):
	"""
	Get stats or get rekt

	:param users: Users JSON as a map
	:param username: User-supplied username, or None to compute all stats
	"""
	print(HOST_NAME + ": Computing stats...\n")
	curr_month = datetime.now().strftime(" [%B %Y]")

	# Compute stats for all users (Extremely stupid algorithm, but works fine)
	if username is None:
		for username in users:
			time = tot_work_time(username)
			if time == 0:
				continue
			# for some reasons line.split(" ") gave problems, so it's best to use line.split()
			print("[+]     Name: " + name_pretty_print(users[username]))
			print("[+] WorkTime: " + time_conv(time) + curr_month + "\n")
	else:
		username = get_normalized_username(username, users)
		print("[+]     Name: " + name_pretty_print(users[username]))
		print("[+] WorkTime: " + time_conv(tot_work_time(username)) + curr_month)


# Convert minutes in a formatted string
def time_conv(minutes):
	return str(int(minutes / 60)) + " h " + str(int(minutes % 60)) + " m"


# Print users list ordered by most active first.
def top(length: int, users: map):
	top_list = []

	# Computing total work time for each member
	for username in users:
		time = tot_work_time(username)
		if time == 0:
			continue
		top_list.append((time, username))

	top_list.sort(reverse=True)

	print(HOST_NAME + ": Hall of Fame (top {})\n".format(str(length)))
	pos = 1
	for i in range(0, min(length, len(top_list))):
		print("[" + str(pos).zfill(2) + "] " + name_pretty_print(users[top_list[i][1]]))
		pos += 1


def main(args_dict):
	# root execution check
	if os.geteuid() == 0:
		print("Error: can't execute " + PROGRAM_NAME + " as root.")
		exit(42)

	if args_dict.get('debug') is True:
		global DEBUG_MODE
		DEBUG_MODE = True
		print(HOST_NAME + ": DEBUG_MODE enabled")

	ensure_log_file()
	users = get_users_file()
	create_backup_if_necessary()

	if args_dict.get('login') is not None:
		login(args_dict.get('login')[0], users)
	elif args_dict.get('logout') is not None:
		logout(args_dict.get('logout')[0], users)
	elif args_dict.get('stat') is not None:
		username = args_dict.get('stat')
		if username is True:
			#  Horrible hack but it works.
			stat(users, None)
		else:
			stat(users, args_dict.get('stat'))
	elif args_dict.get('inlab') is True:
		inlab(users)
	elif args_dict.get('log') is True:
		logfile()
	elif args_dict.get('top') is not None:
		top(args_dict.get('top'), users)
	elif args_dict.get('admin') is True:
		manual_logout(users)
	else:
		print("WTF?")
		exit(69)


# manual_logout()
# sys.stdout.write(COLOR_NATIVE)

if __name__ == '__main__':
	parser = argparse.ArgumentParser(formatter_class=RawDescriptionHelpFormatter, description="""
	WEEELAB v{} - Log management module for garbaging paper sign sheet.
	Author: Stefano Enrico Mendola (aka Hyd3L, STE col teschio)
	Copyright (C) 2017-∞ WEEE Open

	This program comes with ABSOLUTELY NO WARRANTY.
	Since this is a free software, you are welcome
	to redistribute it under the terms of the GNU GPLv3.
	""".format(VERSION))
	# Add commands here, like any normal person instead of hand-coding a parser (or at least make it a LALR(1) parser)
	parser.add_argument('-d', '--debug', action='store_true', help='enable debug mode (don\'t copy files to ownCloud)')
	group = parser.add_argument_group('Actions').add_mutually_exclusive_group(required=True)
	group.add_argument('-i', '--login', type=str, nargs=1, metavar='USER', help='log in USER.')
	group.add_argument('-o', '--logout', type=str, nargs=1, metavar='USER', help='log out USER')
	group.add_argument('-p', '--inlab', action='store_true', help='show who\'s in lab (logged in)')
	group.add_argument('-l', '--log', action='store_true', help='show log file')
	group.add_argument('-t', '--top', type=int, nargs='?', metavar='N', const=10,
	                   help='show top N users by hours spent in lab (default 10)')
	group.add_argument('-s', '--stat', type=str, nargs='?', const=True, metavar='USER',
	                   help='show stats for USER or for eveyone')
	group.add_argument('-a', '--admin', action='store_true', help='enter admin mode')
	args = parser.parse_args()
	main(vars(args))
