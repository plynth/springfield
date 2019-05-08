from springfield import fields, Entity
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


def test_bytes():
    """
    Check that bytes encode/decode to/from json without problems.  And check
    the support for the `encoding` option for BytesField.
    """
    escaping_bytes_field = fields.BytesField(encoding=None)
    hex_bytes_field = fields.BytesField(encoding='hex')
    base64_bytes_field = fields.BytesField()  # base64 is the default

    # Basic check of adapt and jsonify on just bytes
    for input in ('abc', '\x00\xA0\xFF'):
        for f in (escaping_bytes_field, hex_bytes_field, base64_bytes_field):
            # Adapt should reverse jsonify
            assert f.adapt(f.jsonify(input)) == input
            # Since its already bytes, adapt is a no-op
            assert f.adapt(input) == input
        assert escaping_bytes_field.jsonify(input) == input.decode('latin1')
        assert hex_bytes_field.jsonify(input) == unicode(input.encode('hex'))
        assert base64_bytes_field.jsonify(input) == unicode(input.encode('base64'))

    # BytesField doesn't jsonify unicode values
    for input in (u'abc', u'\u0100', u'\u0000'):
        for f in (escaping_bytes_field, hex_bytes_field, base64_bytes_field):
            with pytest.raises(ValueError):
                f.jsonify(input)

    # BytesField doesn't adapt unicode values with code points > 255
    for f in (escaping_bytes_field, hex_bytes_field, base64_bytes_field):
        with pytest.raises(ValueError):
            f.jsonify(u'\u0100')

    # Hex encoding doesn't accept non-hex inputs
    with pytest.raises(TypeError):
        hex_bytes_field.adapt(u'hijklmnop')

    # Should leave null alone
    for f in (escaping_bytes_field, hex_bytes_field, base64_bytes_field):
        assert f.adapt(None) == None
        assert f.jsonify(None) == None


def test_dotted_named_entities():
    """
    Assure that EntityField can be instantiated with dotted-named
    classes.
    """
    class TestEntity(Entity):
        foo = fields.EntityField('tests.dottedname.foo.bar.baz.Zap')

    e = TestEntity(foo={'name': 'baz'})
    assert e.foo.name == 'baz'  # noqa

    # Avoid importing the class before the TestEntity above is instantiated
    # so that we know the `EntityField` import worked as expected.
    from tests.dottedname.foo.bar.baz import Zap
    assert isinstance(e.foo, Zap)


def test_dotted_named_entities_circular_references():
    """
    Assure that circular references in entity fields are handled when
    using dotted-name EntityField types.
    """
    from tests.dottedname.foo.bar.bop import Property

    p = Property(
        name='outer',
        nested={
            'properties': [
                Property(name='inner')
            ]
        }
    )
    assert p
    assert isinstance(p.nested.properties, list)
    assert p.nested.properties[0].name == 'inner'


def test_dotted_named_entities_not_callable():
    """
    Assure that if a dotted-name reference is not callable, that an
    expected error is raised.
    """
    class TestEntity(Entity):
        foo = fields.EntityField('tests.dottedname.foo.bar.baz.NotCallable')

    with pytest.raises(ValueError):
        TestEntity(foo={'name': 'baz'})


def test_dotted_named_entities_not_importable():
    """
    Assure that if invalid references are used, an expected error is raised.
    """
    class RandomStringTestEntity(Entity):
        foo = fields.EntityField('a.string.with.dots')

    with pytest.raises(ValueError):
        RandomStringTestEntity(foo='anything')


def test_dotted_named_entities_not_dotted():
    """
    Assure that byte string references are actually dotted-name references.
    """
    class NonDottedNameEntity(Entity):
        # `Property` is a real class, but this string is not a full
        # reference, so it can't be resolved and is therefore considered
        # invalid.
        foo = fields.EntityField('Property')

    with pytest.raises(ValueError):
        NonDottedNameEntity(foo={})

    class ExistingNonDottedNameEntity(Entity):
        # `FlexEntity` is a real class and it's likely in the local
        # import scope, but it's still not considered a supported
        # dotted-name class reference.
        foo = fields.EntityField('FlexEntity')

    with pytest.raises(ValueError):
        ExistingNonDottedNameEntity(foo={})


    class SelfNonDottedNameEntity(Entity):
        # 'self' is a special case and is the only non-dotted,
        # dotted-name class reference that we support.
        foo = fields.EntityField('self')
        name = fields.StringField()

    result = SelfNonDottedNameEntity(
        name='outer',
        foo={
            'name': 'inner',
            'foo': {
                'name': 'deeper'
            }
        }
    )
    assert result
    assert result.name == 'outer'
    assert result.foo.name == 'inner'
    assert result.foo.foo.name == 'deeper'
