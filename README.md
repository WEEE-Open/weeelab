# weeelab
[![License](http://img.shields.io/:license-GPL3.0-blue.svg)](http://www.gnu.org/licenses/gpl-3.0.html)
![Version](https://img.shields.io/badge/version-2.0-yellow.svg)

Python script for garbaging paper sign sheet.  
The goal of this script is to move to the trash can the paper sign sheet.

## INSTALL

Open a terminal and type these following commands:

    git clone https://github.com/weee-open/weeelab
    cd weeelab
    sudo cp weeelab.py /bin/weeelab

## COMMAND SYNTAX

    usage: weeelab.py [-h] [-d]
                      (-i USER | -o USER | -p | -l | -t [N] | -s [USER] | -a)

    optional arguments:
      -h, --help            show this help message and exit
      -d, --debug           enable debug mode (don't copy files to ownCloud)

    Actions:
      -i USER, --login USER
                            log in USER
      -o USER, --logout USER
                            log out USER
      -p, --inlab           show who's in lab (logged in)
      -l, --log             show log file
      -t [N], --top [N]     show top N users by hours spent in lab (default 10)
      -s [USER], --stat [USER]
                            show stats for USER or for everyone
      -a, --admin           enter admin mode

## NOTES

- The file `log.txt` is filled by appending new lines.
- The file `users.json` contains users info. See the example file and avoid spaces in the fields.
Don't use multiple serial, telegramID or nickname
- The `login` and `logout` functions now work with serial numbers, telegramID and
with nicknames as well.


