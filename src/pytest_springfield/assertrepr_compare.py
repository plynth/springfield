from _pytest.assertion.util import assertrepr_compare
from springfield import Entity


def pytest_assertrepr_compare(config, op, left, right):
    """
    Provide field-by-field comparisons if someone
    uses `assert a==b` to compare two entities.
    """
    left_ent = isinstance(left, Entity)
    right_ent = isinstance(right, Entity)
    if not (left_ent or right_ent):
        return None
    if left_ent:
        left = left.flatten()
    if right_ent:
        right = right.flatten()
    return assertrepr_compare(config, op, left, right)
