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
import argparse
from ldap.filter import escape_filter_chars
import ldap
# For the copyright string in --help
from argparse import RawDescriptionHelpFormatter
from shutil import copy2
# Allows using backspace and arrow keys in input
# noinspection PyUnresolvedReferences
import readline
from getpass import getuser
from datetime import datetime

COLOR_RED = "\033[1;31m"
COLOR_NATIVE = "\033[m"

VERSION = "3.0"
PROGRAM_NAME = __file__.split('/')[-1]

LDAP_SERVER = "ldap.example.com"
LDAP_BIND_DN = "cn=something,dc=example,dc=com"
LDAP_PASSWORD = "foo"
LDAP_TREE = "ou=People,dc=example,dc=com"

HOST_USER = getuser()
DEBUG_MODE = False  # Don't set it here, use -d when running
MAX_WORK_DONE = 2000
LOG_FILENAME = "/home/" + HOST_USER + "/.local/share/" + PROGRAM_NAME + "/log.txt"
BACKUP_PATH = "/home/" + HOST_USER + "/ownCloud/" + PROGRAM_NAME.capitalize() + "/"


# A perfect candidate for dataclasses... which may not be available on an old Python version.
# So no dataclasses.
class User:
	def __init__(self, username: str, full_name: str, first_name: str):
		self.username = username
		self.full_name = full_name
		self.first_name = first_name


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


def matricolize(username: str):
	if username.isdigit():
		return f"s{username}"
	if username[1:].isdigit():
		if username[0] in ('s', 'S', 'd', 'D'):
			return username
	return None


def get_user(username: str) -> User:
	found = False
	ambiguous = False
	matricolized = matricolize(username)
	username = escape_filter_chars(username)
	if matricolized is None:
		filters = (
			f"(&(objectClass=weeeOpenPerson)(uid={username})(!(nsaccountlock=true)))",
			f"(&(objectClass=weeeOpenPerson)(weeelabnickname={username})(!(nsaccountlock=true)))"
		)
	else:
		filters = (
			f"(&(objectClass=weeeOpenPerson)(schacpersonaluniquecode={matricolized})(!(nsaccountlock=true)))",
		)
	del matricolized

	try:
		print(f"Asking {LDAP_SERVER} for info...")
		conn = ldap.initialize(f"ldap://{LDAP_SERVER}:389")
		conn.protocol_version = ldap.VERSION3
		conn.start_tls_s()
		conn.simple_bind_s(LDAP_BIND_DN, LDAP_PASSWORD)
	except ldap.SERVER_DOWN:
		print(f"Cannot connect to LDAP server {LDAP_SERVER}")
		secure_exit(38)
		# noinspection PyTypeChecker
		return None  # Stops complaints from the IDE
	if conn is None:
		print(f"{PROGRAM_NAME}: Error connecting to LDAP server :(")
		secure_exit(38)

	for the_filter in filters:
		result = conn.search_s(LDAP_TREE, ldap.SCOPE_SUBTREE, the_filter, (
			'uid',
			'cn',
			'givenname'
		))
		if len(result) > 1:
			ambiguous = True
		if len(result) == 1:
			attr = result[0][1]
			return User(attr['uid'][0].decode(), attr['cn'][0].decode(), attr['givenname'][0].decode())
	conn.unbind_s()

	if ambiguous:
		print(f"{PROGRAM_NAME}: Multiple accounts found for that username/matricola/nickname, try with another one.")
		secure_exit(2)
	if not found:
		print(f"{PROGRAM_NAME}: Username not recognized. Maybe you misspelled it or you're an intruder.")
		secure_exit(2)


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
			print(f"{PROGRAM_NAME}: creating empty log.txt")
			open(LOG_FILENAME, "a").close()
		else:
			print(f"{PROGRAM_NAME}: cannot find directory {os.path.dirname(LOG_FILENAME)}")
			secure_exit(1)


def store_log_to(filename, destination):
	"""
	Copy a log file (or anything, really) to a directory, if DEBUG_MODE is False

	:param filename: Path to source file
	:param destination: Path to destination file or directory
	"""
	if DEBUG_MODE is True:
		print(f"{PROGRAM_NAME}: DEBUG_MODE, skipped copying {os.path.basename(filename)} to {destination}")
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
			print(f"{PROGRAM_NAME}: Backing up log file to {os.path.basename(stored_log_filename)}")
			os.rename(LOG_FILENAME, stored_log_filename)
			store_log_to(stored_log_filename, BACKUP_PATH)
			print(f"{PROGRAM_NAME}: Done!")

			open(LOG_FILENAME, "a").close()
			print(f"{PROGRAM_NAME}: New log file was created.")
	log_file.close()


def login(username: str, use_ldap: bool):
	"""
	Log in. Add the line in the file. Do it.

	:param use_ldap: Connect to remote LDAP server or blindly trust the input
	:param username: User-supplied username
	"""

	if use_ldap:
		user = get_user(username)
		username = user.username
		pretty_name = user.full_name
	else:
		print(COLOR_RED)
		print("WARNING: bypassing LDAP lookup, make sure that this is the correct username and not an alias")
		print(COLOR_NATIVE)
		pretty_name = username

	if is_logged_in(username):
		print(f"{PROGRAM_NAME}: {pretty_name}, you're already logged in.")
	else:
		curr_time = datetime.now().strftime("%d/%m/%Y %H:%M")
		login_string = f"[{curr_time}] [----------------] [INLAB] <{username}>\n"
		with open(LOG_FILENAME, "a") as log_file:
			log_file.write(login_string)

		store_log_to(LOG_FILENAME, BACKUP_PATH)

		print(f"{PROGRAM_NAME}: Login successful! Hello {pretty_name}!")


def logout(username: str, use_ldap: bool):
	"""
	Log out.

	:param use_ldap: Connect to remote LDAP server or blindly trust the input
	:param username: User-supplied username
	"""
	if not use_ldap:
		print(COLOR_RED)
		print("WARNING: bypassing LDAP lookup, make sure that this is the correct username and not an alias")
		print(COLOR_NATIVE)

	if is_logged_in(username):
		# Using username, and found
		pretty_name = username
	else:
		# Not found, is it an alias?
		if use_ldap:
			# Grab the real username
			user = get_user(username)
			username = user.username
			pretty_name = user.full_name
		if not use_ldap or not is_logged_in(username):
			# Cannot get it from LDAP or still not logged in
			print(f"{PROGRAM_NAME}: you aren't in lab! Did you forget to log in?")
			secure_exit(3)

	curr_time = datetime.now().strftime("%d/%m/%Y %H:%M")
	workdone = ask_work_done()

	if write_logout(username, curr_time, workdone):
		# It's bound, come on...
		# noinspection PyUnboundLocalVariable
		print(f"{PROGRAM_NAME}: Logout successful! Bye {pretty_name}!")
	else:
		print(f"{PROGRAM_NAME}: Logout failed")
		secure_exit(3)


def ask_work_done():
	try:
		workdone = input(f"{PROGRAM_NAME}: What have you done?\n:: ")
		while len(workdone) > MAX_WORK_DONE:
			print(f"{PROGRAM_NAME}: I didn't ask you the story of your life!")
			workdone = input(f"{PROGRAM_NAME}: What have you done? [BRIEFLY]\n:: ")
	except KeyboardInterrupt:
		print(f"{PROGRAM_NAME}: Logout cancelled by keyboard interrupt")
		secure_exit(5)
		return None  # Just prevents PyCharm from complaining
	return workdone


def work_time(timein, timeout) -> str:
	"""
	Returns the time spent in lab formatted as HH:MM
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
def manual_logout():
	sys.stdout.write(COLOR_RED)
	username = input("ADMIN--> insert username: ")

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
	print(f"{PROGRAM_NAME}: Reading log file...\n")
	log_file = open(LOG_FILENAME, "r")
	for line in log_file:
		print(line, end='')
	log_file.close()


def inlab():
	count = 0
	print(f"{PROGRAM_NAME}: Reading log file...\n")
	log_file = open(LOG_FILENAME, "r")
	for line in log_file:
		if "INLAB" in line:
			count += 1
			username = line[47:line.rfind(">")]
			print("> " + username)
	log_file.close()

	if count == 0:
		print(f"{PROGRAM_NAME}: Nobody is in lab right now.")
	elif count == 1:
		print(f"{PROGRAM_NAME}: There is one student in lab right now.")
	else:
		print(f"{PROGRAM_NAME}: There are {count} students in lab right now.")


# Returns total work time in minutes
def tot_work_time(username):
	time_spent = 0
	log_file = open(LOG_FILENAME, "r")
	for line in log_file:
		if (username in line) and not ("INLAB" in line):
			time_spent += ((int(line[39:41]) * 60) + int(line[42:44]))
	log_file.close()
	return time_spent


# Convert minutes in a formatted string
def time_conv(minutes):
	return str(int(minutes / 60)) + " h " + str(int(minutes % 60)) + " m"


def main(args_dict):
	# root execution check
	if os.geteuid() == 0:
		print("Error: can't execute " + PROGRAM_NAME + " as root.")
		exit(42)

	if args_dict.get('debug') is True:
		global DEBUG_MODE
		DEBUG_MODE = True
		print(f"{PROGRAM_NAME}: DEBUG_MODE enabled")
		global LOG_FILENAME
		LOG_FILENAME = "./debug/log.txt"

	ensure_log_file()
	create_backup_if_necessary()

	if args_dict.get('login') is not None:
		login(args_dict.get('login')[0], args_dict.get('ldap'))
	elif args_dict.get('logout') is not None:
		logout(args_dict.get('logout')[0], args_dict.get('ldap'))
	elif args_dict.get('inlab') is True:
		inlab()
	elif args_dict.get('log') is True:
		logfile()
	elif args_dict.get('admin') is True:
		manual_logout()
	else:
		print("WTF?")
		exit(69)


# manual_logout()
# sys.stdout.write(COLOR_NATIVE)

def argparse_this():
	parser = argparse.ArgumentParser(formatter_class=RawDescriptionHelpFormatter, description="""
WEEELAB v{} - Log management module for garbaging paper sign sheet.
Author: Stefano Enrico Mendola (aka Hyd3L, STE col teschio) and others
Copyright (C) 2017-∞ WEEE Open

This program comes with ABSOLUTELY NO WARRANTY.
Since this is a free software, you are welcome
to redistribute it under the terms of the GNU GPLv3.
	""".format(VERSION))
	# Add commands here, like any normal person instead of hand-coding a parser (or at least make it a LALR(1) parser)
	parser.add_argument('-d', '--debug', action='store_true', help='enable debug mode (don\'t copy files to ownCloud)')
	group = parser.add_argument_group('Actions').add_mutually_exclusive_group(required=True)
	group.add_argument('-i', '--login', type=str, nargs=1, metavar='USER', help='log in USER')
	group.add_argument('-o', '--logout', type=str, nargs=1, metavar='USER', help='log out USER')
	group.add_argument('-p', '--inlab', action='store_true', help='show who\'s in lab (logged in)')
	group.add_argument('-l', '--log', action='store_true', help='show log file')
	group.add_argument('-a', '--admin', action='store_true', help='enter admin mode')
	ldap_group_argparse_thing = parser.add_mutually_exclusive_group(required=False)
	ldap_group_argparse_thing.add_argument('--ldap', dest='ldap', action='store_true')
	ldap_group_argparse_thing.add_argument('--no-ldap', dest='ldap', action='store_false')
	ldap_group_argparse_thing.set_defaults(ldap=True)
	args = parser.parse_args()
	return args


if __name__ == '__main__':
	main(vars(argparse_this()))
