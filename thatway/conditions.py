"""Utility condition functions for evaluating values"""

from abc import abstractmethod
from typing import Any, Callable, Protocol, TypeVar, runtime_checkable

__all__ = ("greater_than", "lesser_than", "is_positive", "is_negative", "within")


# Typing protocol to support ordering
@runtime_checkable
class Comparable(Protocol):
    @abstractmethod
    def __lt__(self: "SupportsOrdering", other: "SupportsOrdering") -> bool:
        pass

    @abstractmethod
    def __eq__(self: "SupportsOrdering", other: object) -> bool:
        pass


SupportsOrdering = TypeVar("SupportsOrdering", bound=Comparable)


# Condition functions


def greater_than(other: SupportsOrdering) -> Callable[[SupportsOrdering], bool]:
    """Value must be greater than {other}"""

    def _greater_than(value: SupportsOrdering) -> bool:
        return value > other

    _greater_than.__doc__ = greater_than.__doc__
    return _greater_than


def lesser_than(other: SupportsOrdering) -> Callable[[SupportsOrdering], bool]:
    """Value must be lesser than {other}"""

    def _lesser_than(value: SupportsOrdering) -> bool:
        return value < other

    _lesser_than.__doc__ = greater_than.__doc__
    return _lesser_than


def is_positive(value: SupportsOrdering) -> bool:
    """Value must be positive"""
    if isinstance(value, int):
        return value > 0
    elif isinstance(value, float):
        return value > 0.0
    else:
        raise NotImplementedError


def is_negative(value: SupportsOrdering) -> bool:
    """Value must be negative"""
    if isinstance(value, int):
        return value < 0
    elif isinstance(value, float):
        return value < 0.0
    else:
        raise NotImplementedError


def within(
    minimum: SupportsOrdering, maximum: SupportsOrdering
) -> Callable[[SupportsOrdering], bool]:
    """Value must be within {minimum} and {maximum}."""
    min_func = greater_than(minimum)
    max_func = lesser_than(maximum)

    def _within(value: SupportsOrdering) -> bool:
        return min_func(value) and max_func(value)

    if isinstance(within.__doc__, str):
        _within.__doc__ = within.__doc__.format(minimum=minimum, maximum=maximum)
    return _within


def allowed(*values: Any) -> Callable[[Any], bool]:
    """Value must be one of the following: {values}"""

    def _allowed(value: Any) -> bool:
        return value in values

    if isinstance(allowed.__doc__, str):
        _allowed.__doc__ = allowed.__doc__.format(values=values)

    return _allowed
