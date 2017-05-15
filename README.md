# welab
[![License](http://img.shields.io/:license-GPL3.0-blue.svg)](http://www.gnu.org/licenses/gpl-3.0.html)
![Version](https://img.shields.io/badge/version-1.2.3-blue.svg)

Python script for garbaging paper sign sheet.

The goal of this script is to move to the trash can the paper sign sheet.

## COMMAND SYNTAX
`welab [OPTION] [USER_NAME]`

Available options:  
  `login`  : Sign in to the lab.  
  `logout` : Sign out from the lab.  
  `show`   : Obtain status informations.  
  
  Available infos:  
      `log` : Show log file.  
      `ops` : View a list of operators in lab now.  

## NOTES
- The file `log.dat` is filled by adding new lines on top.
This is important because makes searching for last login easier and it's even more comfortable.
- The file `users.dat` is a simple text file containing usernames in the format
`firstname.lastname serialNumber`, one for each line.
- The `login` and `logout` functions now work with serial numbers and
with nicknames as well.


## ToDo
- [ ] Implement a function to compute stats for a user and for all users and save these stats
to an external file or print them to screen.

- [ ] In function login: add a function to parse the first line of log.dat file in order to discover
if the last logout was in the previous month. If last logout comes from the previous month,
print an error message saying that "it's time for backup" and quit.
Then the operator must move the log.dat file into another folder or into another
storage support in order to backup/print it.
