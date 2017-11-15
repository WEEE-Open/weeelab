# weeelab
[![License](http://img.shields.io/:license-GPL3.0-blue.svg)](http://www.gnu.org/licenses/gpl-3.0.html)
![Version](https://img.shields.io/badge/version-1.4-yellow.svg)

Python script for garbaging paper sign sheet.

The goal of this script is to move to the trash can the paper sign sheet.

## INSTALL
Open a terminal and type these following commands:

    git clone https://github.com/weee-open/weeelab
    cd weeelab
    sudo cp weeelab /bin/weeelab
    cd ..
    rm -fr weeelab

## COMMAND SYNTAX
`weeelab [OPTION] [USER_NAME]`

Available options:  
  `login`  : Sign in to the lab.  
  `logout` : Sign out from the lab.  
  `show`   : Obtain status informations.  
  `top`    : Show a list of top members.  
  `stat`   : Compute stats for a user or for all users.  
  
  Available infos:  
      `log` : Show log file.  
    `inlab` : View a list of operators in lab now.  

## NOTES
- The file `log.dat` is filled by adding new lines on top.
This is important because makes searching for last login easier and it's even more comfortable.
- The file `users.dat` is a simple text file containing usernames in the format
`firstname.lastname serialNumber`, one for each line.
- The `login` and `logout` functions now work with serial numbers and
with nicknames as well.

## ToDo
- [x] Implement a function to compute stats for a user and for all users.
- [x] Implement a function `top` to print a list of users ordered by `most active first`.
- [ ] Improve some algorithms (Long Term Project)
- [ ] Complete rewrite (integrate with bot)

