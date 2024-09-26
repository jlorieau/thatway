"""Project exceptions"""

__all__ = ("SettingException", "ConditionFailure")


class SettingException(Exception):
    """An exception raised from setting, changing or retrieving a setting"""


class ConditionFailure(SettingException):
    """Raised when a condition fails"""
