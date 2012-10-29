# -*- coding: utf-8 -*-

from datetime import timedelta, tzinfo, datetime
import re

try:
    # Try to use pytz if it exists
    from pytz import utc
except ImportError:    
    # Fallback to simple UTC implementation

    class _UtcOffset(tzinfo):
        """
        Simple UTC tzinfo
        """
        def __init__(self):
            self._offset = timedelta(0)
            self._name = 'UTC'

        def utcoffset(self, dt):
            return self._offset

        def tzname(self, dt):
            return self._name

        def dst(self, dt):
            return self._offset

        def __str__(self):
            return self._name

        def __repr__(self):
            return self._name

    #: A :class:`tzinfo` for UTC
    utc = _UtcOffset()

try:
    from dateutil.parser import parse as date_parse
except ImportError:
    import re
    def date_parse(date):
        """
        Parse an RFC3339 formatted time string into a datetime object.

        Assumes input is UTC.
        """
        return datetime(*map(int, re.split(r'[^\d]', date)[:-1])).replace(tzinfo=utc)

try:
    from pyrfc3339 import generate as _generate
    def generate_rfc3339(value):
        """
        Converts a datetime to an RFC3339 formatted time string

        :param value: A :class:`datetime` instance
        """
        return _generate(value, accept_naive=True)

except ImportError:
    def generate_rfc3339(value):
        """
        Converts a datetime to an RFC3339 formatted time string.

        Input is always converted to UTC.

        :param value: A :class:`datetime` instance
        """        
        if value.tzinfo is None:
            value = value.replace(tzinfo=utc)
            
        value = value.astimezone(utc)

        return value.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'

def utcnow():
    """
    Returns the current time in TZ aware UTC.

    :returns: :class:`datetime` instance
    """
    return datetime.now(utc)

