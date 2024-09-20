"""Tests for condition functions"""

from thatway.conditions import (
    allowed,
    greater_than,
    is_negative,
    is_positive,
    lesser_than,
    within,
)


def test_greater_than() -> None:
    """Test the greater_than function"""
    # int
    assert greater_than(3)(5)
    assert not greater_than(3)(2)

    # float
    assert greater_than(3.0)(5.0)
    assert not greater_than(3.0)(2.0)


def test_lesser_than() -> None:
    """Test the lesser_than function"""
    # int
    assert lesser_than(5)(3)
    assert not lesser_than(2)(3)

    # float
    assert lesser_than(5.0)(3.0)
    assert not lesser_than(2.0)(3.0)


def test_is_positive() -> None:
    """Test the is_positive function"""
    # int
    assert is_positive(1)
    assert not is_positive(-1)

    # float
    assert is_positive(1.0)
    assert not is_positive(-1.0)


def test_is_negative() -> None:
    """Test the is_negative function"""
    # int
    assert not is_negative(1)
    assert is_negative(-1)

    # float
    assert not is_negative(1.0)
    assert is_negative(-1.0)


def test_within() -> None:
    """Test the within function"""
    # int
    assert within(5, 10)(7)
    assert not within(5, 10)(4)

    # float
    assert within(5.0, 10.0)(7.0)
    assert not within(5.0, 10.0)(4.0)


def test_allowed() -> None:
    """Test the allowed function"""
    # int
    assert allowed(3, 5, 7)(5)
    assert not allowed(3, 5, 7)(4)

    # float
    assert allowed(3.0, 5.0, 7.0)(5.0)
    assert not allowed(3.0, 5.0, 7.0)(4.0)

    # str
    assert allowed("bananas", "apples", "oranges")("oranges")
    assert not allowed("bananas", "apples", "oranges")("pears")
