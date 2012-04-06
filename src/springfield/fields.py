from datetime import datetime
from anticipate.adapt import adapt, register_adapter, AdaptError

try:
    from dateutil.parser import parse as date_parse
except ImportError:
    import re
    def date_parse(s):
        """Assumes RFC3339 format"""
        return datetime(*map(int, re.split(r'[^\d]', s)[:-1]))

Empty = object()

class FieldDescriptor(object):
    def __init__(self, name, field):
        self.name = name
        self.field = field

    def __get__(self, instance, owner):
        if instance is None:
            return self

        # Get value from document instance if available, if not use default
        value = instance.__values__.get(self.name)
        if value is Empty:
            value = self.field.default
            # Allow callable default values
            if callable(value):
                value = self.field.adapt(value())
            if value is Empty:
                value = None
        return value

    def __set__(self, instance, value):
        instance.__values__[self.name] = self.field.adapt(value)
        instance.__changes__.add(self.name)

class Field(object):
    def __init__(self, default=Empty, *args, **kwargs):
        if callable(default):
            self.default = default
        elif default is not None and default is not Empty:
            self.default = self.adapt(default)
        else:
            self.default = default

    def init(self, cls):
        """
        Intialize the field for its owner class
        """

    def adapt(self, obj):
        """
        Convert the object from one type to the src type.
        """
        return obj

    def make_descriptor(self, name):
        return FieldDescriptor(name=name, field=self)

    def flatten(self, value):
        """
        Get the value as a basic Python type
        """
        return value

    def jsonify(self, value):
        """
        Get the value as a suitable JSON type
        """
        return value


class AdaptableTypeField(Field):
    __adapters__ = None

    type = None
    def adapt(self, obj):
        if obj is None:
            return None
        elif obj is Empty:
            return Empty

        if isinstance(obj, self.type):
            return obj
        elif hasattr(obj, '__adapt__'):
            try:
                return obj.__adapt__(self.type)
            except TypeError as e:
                pass

        if hasattr(self.type, '__adapt__'):
            return self.type.__adapt__(obj)

        if self.__class__.__adapters__ and type(obj) in self.__class__.__adapters__:
            return self.__class__.__adapters__[type(obj)](obj)

        try:
            return adapt(obj, self.type)
        except AdaptError:
            pass

        raise TypeError('Could not adapt %r to %r' % (obj, self.type))


    @classmethod
    def register_adapter(cls, from_cls, func):
        """
        Register a function that can handle adapting from `from_cls` for this field.

        TODO This is probably a bad idea, re-evaluate how to register adapters.
        """
        if not cls.__adapters__:
            cls.__adapters__ = {}

        cls.__adapters__[from_cls] = func

class IntField(AdaptableTypeField):
    type = int
    def adapt(self, obj):
        try:
            return super(IntField, self).adapt(obj)
        except TypeError:
            if isinstance(obj, basestring):
                return int(obj)
            elif isinstance(obj, (float, long)):
                t = int(obj)
                if t == obj:
                    return t

            raise

class FloatField(AdaptableTypeField):
    type = float
    def adapt(self, obj):
        try:
            return super(FloatField, self).adapt(obj)
        except TypeError:
            if isinstance(obj, basestring):
                return float(obj)
            elif isinstance(obj, (float, long)):
                return obj

            raise

class BooleanField(AdaptableTypeField):
    type = bool
    def adapt(self, obj):
        try:
            return super(BooleanField, self).adapt(obj)
        except TypeError:
            if isinstance(obj, basestring):
                str = obj.lower()
                if str in ['yes', 'true', '1', 'on']:
                    return True
                elif str in ['no', 'false', '0', 'off']:
                    return False
            elif isinstance(obj, (float, long, int)):
                if obj == 1:
                    return True
                elif obj == 0:
                    return False

            raise

class StringField(AdaptableTypeField):
    type = unicode
    def adapt(self, obj):
        try:
            return super(StringField, self).adapt(obj)
        except TypeError:
            if isinstance(obj, basestring):
                return unicode(obj)
            raise

class SlugField(StringField):
    pass

class DateTimeField(AdaptableTypeField):
    """
    Field whos value is a Python `datetime.datetime`
    """
    type = datetime

    def adapt(self, obj):
        try:
            return super(DateTimeField, self).adapt(obj)
        except TypeError:
            if isinstance(obj, basestring):
                return date_parse(obj)
            raise

    def jsonify(self, value):
        """
        Get the value as a suitable JSON type
        """
        if value is not None:
            return value.isoformat()

class EmailField(StringField):
    """
    Field that validates as an email address.
    """

class UrlField(StringField):
    pass

class EntityField(AdaptableTypeField):
    def __init__(self, entity, *args, **kwargs):
        """
        :param entity: The entity class to expect for this field. Use `self` to use the class that
                       this field is bound to.
        """
        self.type = entity
        super(EntityField, self).__init__(*args, **kwargs)

    def init(self, cls):
        if self.type == 'self':
            self.type = cls

    def flatten(self, value):
        if value is not None:
            return value.flatten()

    def jsonify(self, value):
        """
        Get the value as a suitable JSON type
        """
        if value is not None:
            return value.jsonify()

class IdField(Field):
    pass

class CollectionField(Field):
    def __init__(self, field, *args, **kwargs):
        self.field = field
        super(CollectionField, self).__init__(*args, **kwargs)

    def adapt(self, obj):
        if obj is not None:
            values = []
            for item in obj:
                values.append(self.field.adapt(item))
            return values

    def flatten(self, value):
        if value is not None:
            values = []
            for item in value:
                values.append(self.field.flatten(item))

            return values

    def jsonify(self, value):
        """
        Get the value as a suitable JSON type
        """
        if value is not None:
            values = []
            for item in value:
                values.append(self.field.jsonify(item))

            return values

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
    for type, field in _type_map.items():
        if isinstance(obj, type):
            return field
    return None
