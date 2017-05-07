# welab
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

## TODO
- [ ] Change login and logout time format to [gg/mm/aaaa hh:mm:ss]
e.g:
[25/12/2018 12:34] [26/12/2018 09:00] john.doe

- [ ] Print to log file the number of hours passed in lab after login and logout time.

- [ ] Implement an input string in function "logout" in order to save to log file a short
      description of work done [max length: about 128 characters]
