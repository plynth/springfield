from springfield import fields
import pytest

def test_slug():
    """
    Assure that slugs are generated properly
    """
    slugify = fields.SlugField().adapt

    for input, expect in [
        ('01 HDR test', '01-hdr-test'),
        ('--&*$#(8$jjsdsd77-----test phrase12 123--', '8jjsdsd77-test-phrase12-123'),
        ('1234', '1234'),
        ('abcdEFG', 'abcdefg'),
    ]:
        assert slugify(input) == expect

def test_float():
    """
    Assure that float can adapt various types
    """
    floatify = fields.FloatField().adapt

    for input, expect in [
        (1.1, 1.1),
        (11, 11.0),
        (long(5.7), 5L)
    ]:
        assert floatify(input) == expect

def test_url():
    """
    Assure that url performs some basic validation
    """
    urlify = fields.UrlField().adapt

    # positive tests
    for input, expect in [
        ('http://www.google.com/SOME/path', 'http://www.google.com/SOME/path'),
        ('http://www.google.com/Path?foo=bar&bar=fOO', 'http://www.google.com/Path?foo=bar&bar=fOO'),
        ('hTTp://www.Google.com', 'http://www.google.com'),
        ('ftp://www.google.com', 'ftp://www.google.com'),
        ('https://www.google.com', 'https://www.google.com'),
        (None, None),
    ]:
        assert urlify(input) == expect

    # negative tests
    for input in [
        'http;//www.google.com',
        'http:/www.google.com',
        'http:www.google.com',
        '<script></script>',
        '<img src="http://foo.bar/badimage">'
    ]:
        with pytest.raises(TypeError):
            urlify(input)
