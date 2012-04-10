import json
import inspect
from springfield.fields import Field, Empty, get_field_for_type
from springfield import fields
from anticipate.adapt import adapt, register_adapter, AdaptError
from anticipate import adapter

class EntityMetaClass(type):
    def __new__(mcs, name, bases, attrs):
        fields = {}
        for base in bases:
            if hasattr(base, '__fields__'):
                fields.update(base.__fields__)

        for key, val in attrs.items():
            if isinstance(val, Field):
                fields[key] = val
                attrs.pop(key)

        for key, field in fields.iteritems():
            attrs[key] = field.make_descriptor(key)

        attrs['__fields__'] = fields

        new_class = super(EntityMetaClass, mcs).__new__(mcs, name, bases, attrs)

        for key, field in fields.items():
            field.init(new_class)

        return new_class

class Entity(object):
    __metaclass__ = EntityMetaClass
    __values__ = None
    __changes__ = None
    __fields__ = None

    def __init__(self, **values):
        # Where the actual values are stored
        object.__setattr__(self, '__values__', {})

        # List of field names that have changed
        object.__setattr__(self, '__changes__', set([]))

        self.update(values)

    def flatten(self):
        """
        Get the values as basic Python types
        """
        data = {}
        for key, val in self.__values__.iteritems():
            val = self.__fields__[key].flatten(val)
            data[key] = val

        return data

    def jsonify(self):
        """
        Return a dictionary suitable for JSON encoding.
        """
        data = {}
        for key, val in self.__values__.iteritems():
            val = self.__fields__[key].jsonify(val)
            data[key] = val
        return data

    def to_json(self):
        """
        Convert the entity to a JSON string.
        """
        return json.dumps(self.jsonify())

    @classmethod
    def from_json(cls, data):
        return cls(**json.loads(data))

    def set(self, key, value):
        self.__setattr__(key, value)

    def get(self, key, default=None, empty=False):
        """
        Get a value by key. If passed an iterable, get a dictionary of values matching keys.

        :param empty: boolean - Include empty values
        """
        if isinstance(key, basestring):
            return getattr(self, key, default)
        else:
            d = {}
            for k in key:
                if empty:
                    d[k] = getattr(self, k, default)
                else:
                    v = self.__values__.get(k, Empty)
                    if v is not Empty:
                        d[k] = v
            return d

    def update(self, values):
        """
        Update attibutes. Ignore keys that aren't fields.
        """
        if hasattr(values, '__values__'):
            for key, val in values.__values__.items():
                if key in self.__fields__:
                    self.set(key, val)
        else:
            for key, val in values.items():
                if key in self.__fields__:
                    self.set(key, val)

    def __setattr__(self, name, value):
        """
        Don't allow setting attributes that haven't been defined as fields.
        """
        if name in self.__fields__:
            object.__setattr__(self, name, value)
        else:
            raise AttributeError('Field %r not defined.' % name)

    @classmethod
    def adapt(cls, obj):
        return adapt(obj, cls)

    @classmethod
    def adapt_all(cls, obj):
        return (adapt(i, cls) for i in obj)

    def __repr__(self):
        return u'<%s %s>' % (self.__class__.__name__, json.dumps(dict(((k, unicode(v)) for k, v in self.__values__.iteritems()))).replace('"', ''))

    def __getstate__(self):
        """Pickle state"""
        return self.__values__

    def __setstate__(self, data):
        """Restore Pickle state"""
        self.__values__ = data

class FlexEntity(Entity):
    """
    An Entity that can have extra attributes added to it.
    """
    __flex_fields__ = None
    def __init__(self, **values):
        object.__setattr__(self, '__flex_fields__', set([]))

        super(FlexEntity, self).__init__(**values)

    def __setattr__(self, name, value):
        if name in self.__fields__:
            object.__setattr__(self, name, value)
        else:
            self.__values__[name] = value
            self.__flex_fields__.add(name)
            self.__changes__.add(name)

    def __getattr__(self, name, default=None):
        return self.__values__.get(name, default)

    def update(self, values):
        for key, val in values.iteritems():
            self.set(key, val)

    def _flatten_value(self, val):
        """
        Have to guess at how to flatten non-fielded values
        """
        if val is None:
            return None
        elif val is Empty:
            return None
        elif isinstance(val, Entity):
            val = val.flatten()
        elif isinstance(val, (tuple, list)) or inspect.isgenerator(val):
            vals = []
            for v in val:
                vals.append(self._flatten_value(v))
            val = vals
        elif isinstance(val, dict):
            data = {}
            for k,v in val.iteritems():
                data[k] = self._flatten_value(v)
            val = data
        elif not isinstance(val, (basestring, int, float, long)):
            val = str(val)
        return val


    def _jsonify_value(self, val):
        if val is None:
            val = None
        elif val is Empty:
            val = None
        elif isinstance(val, Entity):
            val = val.jsonify()
        elif isinstance(val, dict):
            data = {}
            for k,v in val.iteritems():
                data[k] = self._jsonify_value(v)
            val = data
        elif isinstance(val, (tuple, list)) or inspect.isgenerator(val):
            vals = []
            for v in val:
                vals.append(self._jsonify_value(v))
            val = vals
        else:
            field = fields.get_field_for_type(val)
            if field:
                val = field.jsonify(val)

        return val

    def flatten(self):
        """
        Get the values as basic Python types
        """
        data = {}
        for key, val in self.__values__.iteritems():
            if key in self.__fields__:
                val = self.__fields__[key].flatten(val)
            else:
                val = self._flatten_value(val)

            data[key] = val

        return data

    def jsonify(self):
        """
        Get the values as basic Python types
        """
        data = {}
        for key, val in self.__values__.iteritems():
            if key in self.__fields__:
                val = self.__fields__[key].jsonify(val)
            else:
                val = self._jsonify_value(val)

            data[key] = val

        return data

@adapter((Entity, dict), Entity)
def to_entity(obj, to_cls):
    e = to_cls()
    if isinstance(obj, Entity):
        # obj is an Entity
        e.update(obj.flatten())
        return e
    elif isinstance(obj, dict):
        e.update(obj)
        return e

    raise AdaptError('to_entity could not adapt.')


