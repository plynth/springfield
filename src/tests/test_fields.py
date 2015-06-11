from springfield import fields

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
