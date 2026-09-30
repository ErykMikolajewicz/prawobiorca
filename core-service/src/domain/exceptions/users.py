class UserExists(Exception):
    pass


class UserCantLog(Exception):
    pass


class InvalidAccessToken(Exception):
    pass


class InvalidRefreshToken(Exception):
    pass


class UserNotFound(Exception):
    pass
