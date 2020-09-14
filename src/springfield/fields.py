import binascii
import re
import sys
import unicodedata

from codecs import decode, encode
from datetime import datetime

from anticipate.adapt import adapt, AdaptError
from six import integer_types, raise_from, string_types, text_type
from six import reraise as raise_
from six.moves.urllib.parse import urlparse, urlunparse

from springfield.timeutil import date_parse, generate_rfc3339
from springfield.types import Empty
from decimal import Decimal


class FieldDescriptor(object):
    """
    A descriptor that handles setting and getting :class:`Field` values
    on an :class:`Entity`.
    """
    def __init__(self, name, field):
        """
        :param name: The name of the :class:`Entity`'s attribute
        :param field: A :class:`Field` instance
        """
        self.name = name
        self.field = field
        self.__doc__ = self.field.__doc__

    def __get__(self, instance, owner):
        """
        Get the :class:`Field`'s value. If the :class:`Field`'s default
        is a callable, it will be called and adapted if needed.
        """
        if instance is None:
            return self

        return self.field.get(instance, self.name)

    def __set__(self, instance, value):
        """
        Set a value for this :class:`Field`. The value
        is adapted to the :class:`Field`'s type if needed.
        """
        old_value = instance.__values__.get(self.name)
        new_value = self.field.set(instance, self.name, value)
        if new_value != old_value:
            instance.__changes__.add(self.name)


class Field(object):
    """
    A field
    """
    def __init__(self, default=Empty, doc=None, *args, **kwargs):
        """
        :param default: The default value if no value is assigned to this field
        :param doc: The docstring to assign to this field and its descriptor
        """
        if callable(default):
            self.default = default
        elif default is not None and default is not Empty:
            self.default = self.adapt(default)
        else:
            self.default = default

        self.__doc__ = doc

    def init(self, cls):
        """
        Initialize the field for its owner :class:`Entity` class. Any specialization
        that needs to be done based on the :class:`Entity` class itself should be done here.

        :param cls: An :class:`Entity` class.
        """

    def get(self, instance, name):
        # Get value from document instance if available, if not use default
        value = instance.__values__.get(name)
        if value is Empty:
            value = self.default
            # Allow callable default values
            if callable(value):
                value = self.adapt(value())
            if value is Empty:
                value = None
        return value

    def set(self, instance, name, value):
        if value is Empty:
            if name in instance.__values__:
                del instance.__values__[name]
        else:
            instance.__values__[name] = self.adapt(value)
        return instance.__values__[name]

    def adapt(self, value):
        """
        Convert the value from the input type to the expected type if needed.

        :returns: The adapted value
        """
        return value

    def make_descriptor(self, name):
        """
        Create a descriptor for this :class:`Field` to attach to
        an :class:`Entity`.
        """
        return FieldDescriptor(name=name, field=self)

    def flatten(self, value):
        """
        Get the value as a basic Python type

        :param value: An :class:`Entity`'s value for this :class:`Field`
        """
        return value

    def jsonify(self, value):
        """
        Get the value as a suitable JSON type

        :param value: An :class:`Entity`'s value for this :class:`Field`
        """
        return value


class AdaptableTypeField(Field):
    """
    A :class:`Field` that has a specific type and can be adapted
    to another type.
    """

    __adapters__ = None

    #: The value type this :class:`Field` expects
    type = None

    def adapt(self, value):
        """
        Convert the `value` to the `self.type` for this :class:`Field`
        """
        if value is None or value is Empty:
            return value

        if isinstance(value, self.type):
            return value
        elif hasattr(value, '__adapt__'):
            # Use an object's own adapter to adapt.
            try:
                return value.__adapt__(self.type)
            except TypeError:
                pass

        if hasattr(self.type, '__adapt__'):
            # Try using the type's adapter
            return self.type.__adapt__(value)

        if self.__class__.__adapters__:
            # Use a registered adapter
            adapter = self.__class__.__adapters__.get(type(value), None)
            if adapter:
                return adapter(value)

        try:
            # Use generic adapters
            return adapt(value, self.type)
        except AdaptError:
            pass

        raise TypeError('Could not adapt %r to %r' % (value, self.type))

    @classmethod
    def register_adapter(cls, from_cls, func):
        """
        Register a function that can handle adapting from `from_cls` for this
        field.

        TODO This may be a bad idea, re-evaluate how to register adapters.
        """
        if not cls.__adapters__:
            cls.__adapters__ = {}

        cls.__adapters__[from_cls] = func


class IntField(AdaptableTypeField):
    """
    A :class:`Field` that contains an `int`.
    """
    type = int

    def adapt(self, value):
        """
        Adapt `value` to an `int`.

        :param value: Can be an `int`, `float`, `long`, or a
                      `str` or `unicode` that looks like an `int`.

                      `float` or `long` values must represent an
                      integer, i.e. no decimal places.
        """
        try:
            return super(IntField, self).adapt(value)
        except TypeError:
            if isinstance(value, string_types):
                return int(value)
            elif isinstance(value, (float,) + integer_types):
                t = int(value)
                if t == value:
                    return t

            raise


class FloatField(AdaptableTypeField):
    """
    A :class:`Field` that contains a `float`.
    """
    type = float

    def adapt(self, value):
        """
        Adapt `value` to a `float`.

        :param value: Can be an `int`, `float`, `long`, or a
                      `str` or `unicode` that looks like a `float`.

                      `long` values will remain `long`s.
        """
        try:
            return super(FloatField, self).adapt(value)
        except TypeError:
            if isinstance(value, (int,) + string_types):
                return float(value)
            elif isinstance(value, (float,) + integer_types):
                return value
            elif isinstance(value, Decimal):
                return float(value)

            raise


class BooleanField(AdaptableTypeField):
    """
    A :class:`Field` that contains a `bool`.
    """
    type = bool

    def adapt(self, value):
        """
        Adapt `value` to a `bool`.

        :param value: A boolean-like value.

                      A `float`, `int`, or `long` will be converted to:

                          * `True` if equal to `1`
                          * `False` if equal to `0`

                      String values will be converted to (case-insensitive):

                          * `True` if equal to "yes", "true", "1", or "on"
                          * `False` if equal to "no", "false", "0", or "off"
        """
        try:
            return super(BooleanField, self).adapt(value)
        except TypeError:
            if isinstance(value, string_types):
                str = value.lower()
                if str in ['yes', 'true', '1', 'on']:
                    return True
                elif str in ['no', 'false', '0', 'off']:
                    return False
            elif isinstance(value, (float,) + integer_types):
                if value == 1:
                    return True
                elif value == 0:
                    return False

            raise


class StringField(AdaptableTypeField):
    """
    A :class:`Field` that contains a unicode string.
    """
    type = text_type

    def adapt(self, value):
        """
        Adapt `value` to `unicode`.
        """
        try:
            return super(StringField, self).adapt(value)
        except TypeError:
            if isinstance(value, string_types):
                return text_type(value)
            raise


class BytesField(AdaptableTypeField):
    """
    A :class:`Field` that contains binary `bytes`.

    The field has an encoding to use for json/unicode conversion, such
    as `'base64'` (the default) or `'hex'`.

    If `encoding == None`, no encoding/decoding is performed for JSON/unicode
    values which mean JSON itself will have to escape the bytes using unicode
    escapes where necessary.  This is most suitable for cases where the "bytes"
    are known to be ASCII 7-bit safe.

    The encoding is used in `adapt` if the input is a `unicode` instance, and
    in `jsonify` always.
    """

    type = bytes
    encoding = 'base64'

    def __init__(self, encoding='base64', *args, **kwargs):
        """
        Construct a Bytes field

        :param encoding: Optional encoding to use for jsonify(), such as
           'hex' or 'base64'
        """
        super(BytesField, self).__init__(*args, **kwargs)
        self.encoding = encoding

    def jsonify(self, value):
        """
        Encode the bytes into a unicode string suitable for json encoding.

        If an encoding was specified for the field, it is applied here.
        """
        if value is None:
            return None

        if not isinstance(value, bytes):
            raise ValueError('BytesField must contain bytes')

        # Apply hex/base64 encoding if desired
        if self.encoding:
            value = encode(value, self.encoding)

        # Convert to unicode using an 8-bit encoding to retain binary data
        return decode(value, 'latin1')

    def adapt(self, value):
        """
        If the input is unicode, decode it into bytes.  If it is already
        bytes, it is returned unchanged.

        If an encoding was specific for the field, it is applied here if the input
        is `unicode`.

        This assumes that the unicode only contains code points in the
        valid ranges for a byte - e.g. 0-255.

        :param value: Value to decode
        :return: `bytes` object
        """
        if isinstance(value, text_type):
            try:
                value = encode(value, 'latin1')
                if self.encoding:
                    value = decode(value, self.encoding)
            except binascii.Error as e:
                raise_from(TypeError, e)

        return super(BytesField, self).adapt(value)


class SlugField(StringField):
    """
    :class:`Field` whose value is a slugified string.

    A slug is a string converted to lowercase with whitespace
    replace with a "-" and non-ascii chars converted to their
    ascii equivalents.
    """
    def adapt(self, value):
        """
        Adapt `value` to a slugified string.

        :param value: Any string-like value
        """

        # Make sure it's a unicode first
        value = super(SlugField, self).adapt(value)
        if not value:
            return ''

        # re-encoding to ASCII makes it bytes, and we need unicode,
        # so we immediately decode
        slug = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        slug = re.sub(r'[^\w\s-]', '', slug).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')

        return slug


class DateTimeField(AdaptableTypeField):
    """
    :class:`Field` whose value is a Python `datetime.datetime`
    """
    type = datetime

    def adapt(self, value):
        """
        Adapt `value` to a `datetime.datetime` instance.

        :param value: A date-like value. RFC3339 formatted date-strings
                      are supported.

                      If `dateutil` is installed, `dateutil.parser.parse`
                      is used which supports many date formats.
        """
        try:
            return super(DateTimeField, self).adapt(value)
        except TypeError:
            if isinstance(value, string_types):
                return date_parse(value)
            raise

    def jsonify(self, value):
        """
        Get the date as a RFC3339 date-string
        """
        if value is not None:
            return generate_rfc3339(value)


class EmailField(StringField):
    """
    :class:`Field` with an email value
    """


class UrlField(StringField):
    """
    :class:`Field` with a URL value
    """
    def adapt(self, value):
        """
        Validate that the `value` has a valid URL format containing
        a scheme and network location using urlparse.

        :param value: A url-like value.

        :returns: URL with sheme and network location in lower case.
        """
        value = super(UrlField, self).adapt(value)
        if value:
            url_parts = urlparse(value)
            if url_parts.scheme and url_parts.netloc:
                new_url_parts = list(url_parts)
                new_url_parts[0] = url_parts.scheme.lower()
                new_url_parts[1] = url_parts.netloc.lower()
                return urlunparse(new_url_parts)

            raise TypeError('URL: %s is not a valid URL format' % value)


class EntityField(AdaptableTypeField):
    """
    :class:`Field` that can contain an :class:`Entity`
    """

    # A map storing resolved dotted-name class types
    _dotted_name_types = {}

    def __init__(self, entity, *args, **kwargs):
        """
        :param entity: The :class:`Entity` class to expect for this field.
                       Use 'self' to use the :class:`Entity` class that
                       this field is already bound to.
        """
        self._type = entity
        super(EntityField, self).__init__(*args, **kwargs)

    @staticmethod
    def _resolve_dotted_name(dotted_name):
        try:
            if '.' in dotted_name:
                modules, _kls_name = dotted_name.rsplit('.', 1)
                _module = __import__(modules, fromlist=[_kls_name])
                _kls = getattr(_module, _kls_name)
                assert callable(_kls), 'Dotted-name entity types should be callable.'
                return _kls
            elif 'self' != dotted_name:
                raise ValueError('Invalid class name for EntityField: %s' % dotted_name)
        except Exception:
            raise_(
                ValueError,
                ValueError('Invalid class name for EntityField: %s' % dotted_name),
                sys.exc_info()[2]
            )

    @property
    def type(self):
        """
        Determine the type of the Entity that will be instantiated.

        There are three ways to reference an Entity when using an EntityField:

        - 'self': A byte string referencing the class that is defining this
            EntityField as an attribute.
        - '{dotted.name.kls}': A byte string referencing an importable callable
            that can be instantiated at field-instantiation time.
        - {Entity}: A type that subclasses `Entity`.

        The order of operations during instantiation and resolution of the
        above references is important; During the creation of an `Entity`, the
        metaclass will call `init()` for fields defined on the class. This
        is useful for the 'self' reference so that the `EntityField` can
        be initialized with the class that is being instantiated during
        creation of the instance. For dotted-name class strings, this is too
        early since the dotted-name reference may not exist yet. For this
        reason, resolving the dotted-name reference is deferred to be as late
        as possible, in this case on the first read of the `type` property of
        this field.

        The dotted-name references are stored in a map on the `EntityField`
        class to prevent resolving and importing the dotted-name on every
        instance of this `EntityField`.

        Returns:
            `type`: A type to use when instantiating the Entity for this
                EntityField.

        """
        if isinstance(self._type, (bytes, text_type)):
            if self._type not in self.__class__._dotted_name_types:
                _kls = self._resolve_dotted_name(self._type)
                self.__class__._dotted_name_types[self._type] = _kls
            return self.__class__._dotted_name_types[self._type]

        return self._type

    def init(self, cls):
        if self._type == 'self':
            self._type = cls

    def flatten(self, value):
        """
        Convert an :class:`Entity` to a `dict` containing native
        Python types.
        """
        if value is not None:
            return value.flatten()

    def jsonify(self, value):
        """
        Convert an :class:`Entity` into a JSON object
        """
        if value is not None:
            return value.jsonify()


class IdField(Field):
    """
    A :class:`Field` that is used as the primary identifier for an :class:`Entity`

    TODO This should accept another Field type to contain the ID
    """


class CollectionField(Field):
    """
    A :class:`Field` that can contain an ordered list of values matching
    a specific :class:`Field` type.
    """

    #: The :class:`Field` this collection contains
    field = None

    def __init__(self, field, *args, **kwargs):
        if not isinstance(field, Field):
            field = field()
        self.field = field
        super(CollectionField, self).__init__(*args, **kwargs)

    def init(self, cls):
        self.field.init(cls)

    def adapt(self, value):
        """
        Adapt all values of an iterable to the :class:`CollectionField`'s
        field type.
        """
        if value is not None:
            values = []
            for item in value:
                values.append(self.field.adapt(item))
            return values

    def flatten(self, value):
        """
        Convert all values of an iterable to the :class:`CollectionField`'s
        field type's native Python type.
        """
        if value is not None:
            values = []
            for item in value:
                values.append(self.field.flatten(item))

            return values

    def jsonify(self, value):
        """
        Convert all values of an iterable to the :class:`CollectionField`'s
        field type's JSON type.
        """
        if value is not None:
            values = []
            for item in value:
                values.append(self.field.jsonify(item))

            return values


#: Map basic types to fields
_type_map = {
    datetime: DateTimeField(),
    int: IntField(),
    bytes: BytesField(),
    str: StringField(),
    text_type: StringField(),
    float: FloatField(),
    bool: BooleanField(),
}


def get_field_for_type(obj):
    t = type(obj)
    if t in _type_map:
        return _type_map[t]
    for typ, field in _type_map.items():
        if isinstance(obj, typ):
            return field
    return None
