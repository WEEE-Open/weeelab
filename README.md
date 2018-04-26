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
`weeelab.py [OPTION] [USER_NAME]`

Available options:  
  `login <username>`  : Sign in to the lab.    
  `logout <username>` : Sign out from the lab.    
  `show <option>` : Obtain status informations. Options available:
   - `log` : Show log file.  
   - `inlab` : View a list of operators in lab now.
   
  `top <int>`: Show a list of \<int\> top members. \<int\> is optional.     
  `stat <username>`   : Compute stats for a user or for all users.  
  

## NOTES
- The file `log.dat` is filled by adding new lines.
- The file `users.json` contain users info. See the example file and avoid spaces in the fields. 
Don't use multiple serial, telegramID or nickname
- The `login` and `logout` functions now work with serial numbers, telegramID and
with nicknames as well.


