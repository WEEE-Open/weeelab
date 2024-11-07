"""
Define the functions:
 - login()
 - logout()
 - ask_action()

 These connect with LDAP and perform the login and use the db module to interact with the database.
"""
def login(user: str):
    """
    user can be any of the identifiers in the LDAP server.
    Retrieve the username, name and surname from LDAP.
    If the user is not in LDAP, return an error.
    If the user didn't sign the sir, print a warning.
    Call the db.login function to log the user in.
    """
    pass

def logout(user: str):
    """
    user can be any of the identifiers in the LDAP server.
    If the user is not in LDAP, return an error.
    Call the db.logout function to log the user out.
    """
    pass

def ask_action():
    """
    Ask the user if they want to login or logout.
    """
    pass