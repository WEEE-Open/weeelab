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

## NOTES
- The file `log.dat` is filled by adding new lines on top. This is important because
makes searching for last login easier and it's even more comfortable.
- The file `users.dat` is a simple text file containing usernames in the format
firstname.lastname, one for each line.


## TODO
- [ ] Change login and logout time format to [gg/mm/aaaa hh:mm:ss]
      e.g: [25/12/2018 12:34] [26/12/2018 09:00] john.doe

- [ ] Print to log file the number of hours passed in lab after login and logout time. (logout function)
      e.g: [11/04/2017 11:30] [11/04/2017 13:00] 01:30 john.doe


- [ ] Implement an input string in function "logout" in order to save to log file a short
      description of the work done [max length: about 128 characters]
      e.g: [11/04/2017 11:30] [11/04/2017 13:00] 01:30 john.doe : Won for two times at Windows 95's solitaire.

- [ ] Implement a function to calculate stats for a user and for all users and save these stats
      to an external file or print them to screen.

- [ ] In function login: add a function to parse the first line of log.dat file in order to discover
      if the last logout was in the previous month. If last logout comes from the previous month,
      print an error message saying that "it's time for backup" and quit.
      Then the operator must move the log.dat file into another folder or into another
      storage support in order to backup/print it.

