from datetime import datetime
import unicodedata
from anticipate.adapt import adapt, AdaptError
from springfield.timeutil import date_parse, generate_rfc3339
from springfield.types import Empty
from decimal import Decimal
import re

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
            except TypeError as e:
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
            if isinstance(value, basestring):
                return int(value)
            elif isinstance(value, (float, long)):
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
            if isinstance(value, (basestring, int)):
                return float(value)
            elif isinstance(value, (float, long)):
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
            if isinstance(value, basestring):
                str = value.lower()
                if str in ['yes', 'true', '1', 'on']:
                    return True
                elif str in ['no', 'false', '0', 'off']:
                    return False
            elif isinstance(value, (float, long, int)):
                if value == 1:
                    return True
                elif value == 0:
                    return False

            raise

class StringField(AdaptableTypeField):
    """
    A :class:`Field` that contains a unicode string.
    """

    type = unicode
    def adapt(self, value):
        """
        Adapt `value` to `unicode`.
        """
        try:
            return super(StringField, self).adapt(value)
        except TypeError:
            if isinstance(value, basestring):
                return unicode(value)
            raise

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

        slug = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
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
            if isinstance(value, basestring):
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

class EntityField(AdaptableTypeField):
    """
    :class:`Field` that can contain an :class:`Entity`
    """
    def __init__(self, entity, *args, **kwargs):
        """
        :param entity: The :class:`Entity` class to expect for this field.
                       Use 'self' to use the :class:`Entity` class that
                       this field is already bound to.
        """
        self.type = entity
        super(EntityField, self).__init__(*args, **kwargs)

    def init(self, cls):
        if self.type == 'self':
            self.type = cls

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
    basestring: StringField(),
    unicode: StringField(),
    str: StringField(),
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
