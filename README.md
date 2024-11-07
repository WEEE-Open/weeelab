# weeelab
[![License](http://img.shields.io/:license-GPL3.0-blue.svg)](http://www.gnu.org/licenses/gpl-3.0.html)
![Version](https://img.shields.io/badge/version-2.0-yellow.svg)

Python module for garbaging paper sign sheet.  
The goal is to move to the trash can the paper sign sheet.

v1.5 is supposed to be provisional, until ![grillo](https://github.com/WEEE-Open/grillo) is ready for production.
To make the switch easier when the time to migrate comes, it shares the same database structure even if it's overkill for just weeelab.

## INSTALL
First setup the database, from https://github.com/WEEE-Open/grillo/blob/master/docker/db/
You can either create a native postgres db or use the provided Dockerfile to containerize it.

Then, open a terminal and type:

```sh
pip install weeelab
```

Then create a file named `config.toml` in `~/.config/WEEE Open/weeelab` with the following variables:

```shell script
[db]
name = "grillo"
host = "localhost"
port = 5432
user = "weeelab"
password = "asd"

[ldap]
host = "ldap.example.com"
bind_dn = "cn=something,dc=example,dc=com"
password = "foo"
tree = "ou=People,dc=example,dc=com"
```

## COMMAND SYNTAX

```
Usage: weeelab [OPTIONS]

Options:
  -h, --help            Show this message and exit
  -v, --version         Show the version and exit
  -d, --debug           Print all logs
  -u, --user            Specify the user to login/logout.
  -m, --message         Specify the message on logout. Implies `-a logout`, will be ignored if login is specified.
  -a, --action          Specify the action to perform. Can be login or logout.
```

The command always needs an action and a user and will prompt for them if they're not specified in the options.
If the action is logout, the same is true for message.

## License

GNU GPL v3 except for icons:

- **login.png**: Icons made by <a href="https://www.flaticon.com/authors/mavadee" title="mavadee">mavadee</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a>
- **logout.png**: Icons made by <a href="https://www.flaticon.com/authors/mavadee" title="mavadee">mavadee</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a>
