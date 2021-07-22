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
# For the copyright string in --help
from argparse import RawDescriptionHelpFormatter
from shutil import copy2
# Allows using backspace and arrow keys in input
# noinspection PyUnresolvedReferences
import readline
from getpass import getuser
from datetime import datetime
from time import sleep
from typing import Optional
from dotenv import load_dotenv
from select import select
import subprocess
import os

if '--no-ldap' not in sys.argv:
	from ldap.filter import escape_filter_chars
	import ldap

load_dotenv(os.path.join(os.path.dirname(os.path.realpath(__file__)), '.env'))

COLOR_RED = "\033[1;31m"
COLOR_NATIVE = "\033[m"

VERSION = "3.2"
PROGRAM_NAME = __file__.split('/')[-1]
HOST_USER = getuser()
DEBUG_MODE = False  # Don't set it here, use -d when running
MAX_WORK_DONE = 2000

LDAP_SERVER = os.getenv("LDAP_SERVER")
LDAP_BIND_DN = os.getenv("LDAP_BIND_DN")
LDAP_PASSWORD = os.getenv("LDAP_PASSWORD")
LDAP_TREE = os.getenv("LDAP_TREE")
LOG_PATH = os.getenv("LOG_PATH")
LOG_FILENAME = LOG_PATH + "/log.txt"
FIRST_IN = os.getenv("FIRST_IN_SCRIPT_PATH")
LAST_OUT = os.getenv("LAST_OUT_SCRIPT_PATH")

FIRST_IN_HAPPENED = False
LAST_OUT_HAPPENED = False

# BACKUP_PATH = "/home/" + HOST_USER + "/ownCloud/" + PROGRAM_NAME.capitalize() + "/"


# A perfect candidate for dataclasses... which may not be available on an old Python version.
# So no dataclasses.
class User:
	def __init__(self, username: str, full_name: str, first_name: str):
		self.username = username
		self.full_name = full_name
		self.first_name = first_name


class LdapError(BaseException):
	def __init__(self):
		pass


class UserNotFoundError(BaseException):
	def __init__(self):
		pass

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
		# print(f"Asking {LDAP_SERVER} for info...")
		conn = ldap.initialize(f"ldap://{LDAP_SERVER}:389")
		conn.protocol_version = ldap.VERSION3
		conn.start_tls_s()
		conn.simple_bind_s(LDAP_BIND_DN, LDAP_PASSWORD)
	except ldap.SERVER_DOWN:
		print(f"Cannot connect to LDAP server {LDAP_SERVER}")
		raise LdapError
	if conn is None:
		print(f"Error connecting to LDAP server :(")
		raise LdapError

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
		print(f"Multiple accounts found for that username/matricola/nickname, try with another one.")
		raise UserNotFoundError
	if not found:
		print(f"Username not recognized. Maybe you misspelled it or you're an intruder.")
		raise UserNotFoundError


def is_logged_in(username: str) -> bool:
	"""
	Check if user is already logged in.

	:param username: normalized username
	:return:
	"""
	logged = False
	with open(LOG_FILENAME, "r") as log_file:
		for line in log_file:
			if inlab_line(line) and user_in_line(line, username):
				logged = True
				break
	return logged


def people_in_lab() -> int:
	count = 0
	with open(LOG_FILENAME, "r") as log_file:
		for line in log_file:
			if inlab_line(line):
				count += 1
	return count


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
	if not os.path.exists(LOG_FILENAME):
		if os.path.isdir(os.path.dirname(LOG_FILENAME)):
			print(f"Creating empty log.txt")
			open(LOG_FILENAME, "a").close()
		else:
			print(f"Cannot find directory {os.path.dirname(LOG_FILENAME)}")
			secure_exit(1)


def store_log_to(filename, destination):
	"""
	Copy a log file (or anything, really) to a directory, if DEBUG_MODE is False

	:param filename: Path to source file
	:param destination: Path to destination file or directory
	"""
	if DEBUG_MODE:
		print(f"DEBUG_MODE, skipped copying {os.path.basename(filename)} to {destination}")
	else:
		copy2(filename, destination)


def create_backup_if_necessary():
	# Open master log file
	with open(LOG_FILENAME, "r") as log_file:
		if not is_empty(log_file):  # If current log file is not empty
			last_month_year = str(log_file.read())[4:11]

			curr_month = int(datetime.now().strftime("%m"))
			curr_year = int(datetime.now().strftime("%Y"))
			last_date = datetime.strptime(last_month_year, "%m/%Y")
			last_month = int(last_date.strftime("%m"))
			last_year = int(last_date.strftime("%Y"))

			# If the inexorable passage of time has been perceived by this program, too...
			if (curr_month > last_month) or (curr_year > last_year):
				# log.txt -> log201901.txt, foo.txt -> foo201901.txt, etc...
				stored_log_filename = LOG_FILENAME.rsplit('.', 1)[0] + last_date.strftime("%Y%m") + ".txt"
				print(f"Backing up log file to {os.path.basename(stored_log_filename)}")
				os.rename(LOG_FILENAME, stored_log_filename)
				# store_log_to(stored_log_filename, BACKUP_PATH)
				# print(f"Done!")

				open(LOG_FILENAME, "a").close()
				print(f"New log file was created.")


def login(username: str, use_ldap: bool):
	"""
	Log in. Add the line in the file. Do it.

	:param use_ldap: Connect to remote LDAP server or blindly trust the input
	:param username: User-supplied username
	"""

	lab_was_empty = people_in_lab() == 0

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
		print(f"{pretty_name}, you're already logged in.")
	else:
		curr_time = datetime.now().strftime("%d/%m/%Y %H:%M")
		login_string = f"[{curr_time}] [----------------] [INLAB] <{username}>\n"
		with open(LOG_FILENAME, "a") as log_file:
			log_file.write(login_string)

		# store_log_to(LOG_FILENAME, BACKUP_PATH)

		if lab_was_empty:
			global FIRST_IN_HAPPENED
			FIRST_IN_HAPPENED = True
		print(f"Login successful! Hello {pretty_name}!")


def logout(username: str, use_ldap: bool, message: Optional[str] = None):
	"""
	Log out.

	:param message: Logout message, None to ask
	:param use_ldap: Connect to remote LDAP server or blindly trust the input
	:param username: User-supplied username
	"""

	last_person = people_in_lab() == 1

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
			new_username = user.username
			pretty_name = user.full_name
			if username == new_username or not is_logged_in(new_username):
				print(f"You aren't in lab! Did you forget to log in?")
				return False
			username = new_username
		else:
			# Cannot get it from LDAP
			print(f"You aren't in lab! Did you use an alias or ID number? These do not work right now")
			return False

	curr_time = datetime.now().strftime("%d/%m/%Y %H:%M")
	if message is None:
		workdone = ask_work_done()
	else:
		workdone = message

	if write_logout(username, curr_time, workdone):
		if last_person:
			global LAST_OUT_HAPPENED
			LAST_OUT_HAPPENED = True
		print(f"Logout successful! Bye {pretty_name}!")
		return True
	else:
		print(f"Logout failed")
		return False


def ask_work_done():
	try:
		workdone = input(f"What have you done?\n:: ")
		while len(workdone) > MAX_WORK_DONE:
			print(f"I didn't ask you the story of your life!")
			workdone = input(f"What have you done? [BRIEFLY]\n:: ")
	except KeyboardInterrupt:
		print(f"Logout cancelled by keyboard interrupt")
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


def inlab_line(line: str) -> bool:
	# [02/05/2017 10:00] [----------------] [INLAB] :: <
	return line[39:44] == "INLAB"


def user_in_line(line: str, username: str) -> bool:
	username_in_line = line.split('<', 1)[1].split('>', 1)[0]
	return username == username_in_line


def write_logout(username, curr_time, workdone) -> bool:
	"""
	I don't even want to know. This thing works, it's ok, don't touch it
	"""
	found = False

	log_list = []
	with open(LOG_FILENAME, "r") as log_file:
		for line in log_file:
			if inlab_line(line) and user_in_line(line, username):
				found = True
				login_time = line[12:17]
				logout_time = curr_time[11:17]
				line = line.replace("----------------", curr_time)
				line = line.replace("INLAB", work_time(login_time, logout_time))
				line = line.replace("\n", "")

				line = line + " :: " + workdone + "\n"
			log_list.append(line)  # Store everything in the list

	if found:
		# add .lock file during writing process if there isn't one, wait until it's removed, then re-add it
		while True:
			try:
				with open(LOG_FILENAME+'.lock', 'x'):
					break
			except FileExistsError:
				sleep(.5)

		# Writing everything to log file
		with open(LOG_FILENAME, "w") as log_file:
			for line in log_list:
				log_file.write(line)

		# remove .lock file
		os.remove(LOG_FILENAME+'.lock')

		# store_log_to(LOG_FILENAME, BACKUP_PATH)

	return found


# logout by passing manually date and time
def manual_logout():
	sys.stdout.write(COLOR_RED)
	username = input("ADMIN--> insert username: ")

	date = input("ADMIN--> insert date (gg/mm/aaaa): ")
	if not check_date(date):
		return False

	hour = input("ADMIN--> insert time (hh:mm): ")
	if not check_hour(hour):
		return False

	curr_time = date + " " + hour

	workdone = ask_work_done()

	print("ADMIN--> you will update the log file with ")
	print("            " + username + " " + curr_time)
	answer = input("ADMIN--> are you sure? (y/n)")
	if answer != "y":
		return False

	if write_logout(username, curr_time, workdone):
		print("ADMIN--> Update succeeded")
	else:
		print("ADMIN--> Update failed (not logged in?)")


def logfile():
	print(f"Reading log file...\n")
	with open(LOG_FILENAME, "r") as log_file:
		for line in log_file:
			print(line, end='')


def inlab():
	count = 0
	print(f"Reading log file...\n")
	with open(LOG_FILENAME, "r") as log_file:
		for line in log_file:
			if inlab_line(line):
				count += 1
				username = line[47:line.rfind(">")]
				print("> " + username)

	if count == 0:
		print(f"Nobody is in lab right now.")
	elif count == 1:
		print(f"There is one student in lab right now.")
	else:
		print(f"There are {count} students in lab right now.")


# Returns total work time in minutes
def tot_work_time(username):
	time_spent = 0
	with open(LOG_FILENAME, "r") as log_file:
		for line in log_file:
			if user_in_line(username, line) and not inlab_line(line):
				time_spent += ((int(line[39:41]) * 60) + int(line[42:44]))
	return time_spent


# Convert minutes in a formatted string
def time_conv(minutes):
	return str(int(minutes / 60)) + " h " + str(int(minutes % 60)) + " m"


def interactive_log(in_: bool, use_ldap: bool):
	retry = True
	retry_username = None
	while retry:
		try:
			if retry_username:
				username = retry_username
				retry_username = None
			else:
				username = input("Type your name.surname OR id (matricola) OR nickname OR swipe the card on the reader:\n")
				matricola_scan = read_from_card_reader(username)
				if matricola_scan:  # Input with magnetic card
					username = matricola_scan

			try:
				if in_:
					login(username, use_ldap)
					return True
				else:
					res = logout(username, use_ldap)
					if res:
						return True
			except LdapError:
				retry_ldap_question = True
				print(f"Hmmm... It seems the network or the LDAP server has some problems.")
				while retry_ldap_question:
					choice = input("Type R to retry or D to disable LDAP lookup: [R/D] ")
					choice = choice.strip().upper()
					if choice == 'R':
						retry_username = username
						retry_ldap_question = False
					elif choice == 'D':
						use_ldap = False
						retry_ldap_question = False
			except UserNotFoundError:
				pass
		except KeyboardInterrupt:
			print(f"Keyboard interrupt detected, interactive log{'in' if in_ else 'out'} cancelled")
			return False
		except EOFError:
			print(f"EOF detected, interactive log{'in' if in_ else 'out'} cancelled")
			return False


def read_from_card_reader(text) -> Optional[str]:
	direction = None
	if text[0] == "ò":
		if text[-1] == "-":
			direction = "left"
		elif text[-1] == "_":
			direction = "right"
	elif text[0] == ";":
		if text[-1] == "/":
			direction = "left"
		elif text[-1] == "?":
			direction = "right"

	if direction is not None:
		matricola = text[9:15]
		print(f"Detected card scan from {direction} with matricola {matricola}")
		return matricola
	return None


def main(args_dict):
	# root execution check
	if os.geteuid() == 0:
		print("Error: can't execute " + PROGRAM_NAME + " as root.")
		exit(42)

	if args_dict.get('debug'):
		global DEBUG_MODE
		DEBUG_MODE = True
		print(f"DEBUG_MODE enabled")
		global LOG_FILENAME
		LOG_FILENAME = "./debug/log.txt"

	ensure_log_file()
	create_backup_if_necessary()

	result = True
	interactive = False
	try:
		if args_dict.get('login'):
			login(args_dict.get('login')[0], args_dict.get('ldap'))
		elif args_dict.get('logout'):
			if args_dict.get('message') is None:
				message = None
			else:
				message = args_dict.get('message')[0]
			result = logout(args_dict.get('logout')[0], args_dict.get('ldap'), message)
		elif args_dict.get('interactive_login'):
			interactive = True
			result = interactive_log(True, args_dict.get('ldap'))
		elif args_dict.get('interactive_logout'):
			interactive = True
			result = interactive_log(False, args_dict.get('ldap'))
		elif args_dict.get('inlab'):
			inlab()
		elif args_dict.get('log'):
			logfile()
		elif args_dict.get('admin'):
			result = manual_logout()
		else:
			print("WTF?")
			exit(69)
	except LdapError:
		result = False
	except UserNotFoundError:
		result = False

	auto_close = True

	if FIRST_IN_HAPPENED:
		if FIRST_IN:
			if os.path.isfile(FIRST_IN):
				print("I'm now launching the \"first in\" script, but you can close this window")
				subprocess.Popen([FIRST_IN])
			else:
				print(f"The \"first in\" script \"{FIRST_IN}\" does not exist, notify an administrator")

	if LAST_OUT_HAPPENED:
		if LAST_OUT:
			if os.path.isfile(LAST_OUT):
				print("I'm now launching the \"last out\" script, but you can close this window")
				subprocess.Popen([LAST_OUT])
			else:
				print(f"The \"last out\" script \"{LAST_OUT}\" does not exist, notify an administrator")

	# if SIR:
	#   auto_close = False

	if interactive:
		if auto_close and result:
			print("Press enter to exit (or wait 10 seconds)")
			# does not work on windows:
			select([sys.stdin], [], [], 10)
		else:
			print("Press enter to exit")
			# does not work on windows:
			input()

	if not result:
		secure_exit(3)


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
	group.add_argument('--interactive-login', action='store_true', help='log in with questions')
	group.add_argument('--interactive-logout', action='store_true', help='log out with questions')
	parser.add_argument('-m', '--message', type=str, nargs=1, metavar='MESSAGE', help='logout message')
	group.add_argument('-p', '--inlab', action='store_true', help='show who\'s in lab (logged in)')
	group.add_argument('-l', '--log', action='store_true', help='show log file')
	group.add_argument('-a', '--admin', action='store_true', help='enter admin mode')
	ldap_group_argparse_thing = parser.add_mutually_exclusive_group(required=False)
	ldap_group_argparse_thing.add_argument('--ldap', dest='ldap', action='store_true')
	ldap_group_argparse_thing.add_argument('--no-ldap', dest='ldap', action='store_false')
	ldap_group_argparse_thing.set_defaults(ldap=True)
	args = parser.parse_args()
	if args.message is not None and args.logout is None:
		parser.error("You can't set a logout message alone or for other commands other than logout.\n"
					 "You can use -m or its equivalent --message only if you also use the -o or --logout parameter.")
	return args


if __name__ == '__main__':
	main(vars(argparse_this()))
