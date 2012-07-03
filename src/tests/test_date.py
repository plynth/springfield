from springfield.timeutil import date_parse, generate_rfc3339, utcnow
from datetime import timedelta

def test_rfc3339():
    """
    Assure that RFC3339 formatting is working.

    Warning: This test could get different results depending on if pytz and dateutil is installed.
    """

    n = utcnow()
    offset = n.tzinfo.utcoffset(n)
    assert offset == timedelta(0)

    str = generate_rfc3339(n)
    
    assert 'T' in str
    assert str.endswith('Z')

    dt = date_parse(str)

    # `generate_rfc3339` does not convert microseconds so we can't compare them
    odt = n.replace(microsecond=0)

    assert dt == odt