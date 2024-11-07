class LdapError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class DBConnectionError(Exception):
    pass


class UserLoggedInError(Exception):
    pass


class UserNotLoggedInError(Exception):
    pass
