import json
import inspect
from six import integer_types, string_types, text_type, with_metaclass
from springfield.fields import Field, Empty
from springfield.alias import Alias
from springfield import fields
from anticipate.adapt import adapt, AdaptError
from anticipate import adapter


class EntityBase(object):
    """
    An empty class that does nothing but allow us to determine
    if an Entity references other Entities in the EntityMetaClass.

    We can't do this with Entity directly since Entity can't exist
    until EntityMetaClass is created but EntityMetaClass can't compare
    against Entity since it doesn't exist yet.
    """


class EntityMetaClass(type):
    def __new__(mcs, name, bases, attrs):
        _fields = {}
        aliases = {}
        for base in bases:
            if hasattr(base, '__fields__'):
                _fields.update(base.__fields__)
            if hasattr(base, '__aliases__'):
                _fields.update(base.__aliases__)

        for key, val in list(attrs.items()):
            is_cls = inspect.isclass(val)

            if isinstance(val, Field):
                _fields[key] = val
                attrs.pop(key)
            elif isinstance(val, Alias):
                aliases[key] = val
                attrs.pop(key)
            elif is_cls and issubclass(val, Field):
                _fields[key] = val()
                attrs.pop(key)
            elif isinstance(val, EntityBase) or (is_cls and issubclass(val, EntityBase)):
                # Wrap fields assigned to `Entity`s with an `EntityField`
                _fields[key] = fields.EntityField(val)
                attrs.pop(key)
            elif isinstance(val, list) and len(val) == 1:
                attr = val[0]
                is_cls = inspect.isclass(attr)
                if isinstance(attr, EntityBase) or (is_cls and issubclass(attr, EntityBase)):
                    # Lists that contain just an Entity class are treated as
                    # a collection of that Entity
                    _fields[key] = fields.CollectionField(fields.EntityField(attr))
                elif isinstance(attr, Field) or (is_cls and issubclass(attr, Field)):
                    # Lists that contain just a Field class are treated as
                    # a collection of that Field
                    _fields[key] = fields.CollectionField(attr)

        for key, field in _fields.items():
            attrs[key] = field.make_descriptor(key)

        for key, field in aliases.items():
            attrs[key] = field.make_descriptor(key)

        attrs['__fields__'] = _fields
        attrs['__aliases__'] = aliases

        new_class = super(EntityMetaClass, mcs).__new__(mcs, name, bases, attrs)

        for key, field in _fields.items():
            field.init(new_class)

        for key, field in aliases.items():
            field.init(new_class)

        return new_class


class Entity(with_metaclass(EntityMetaClass, EntityBase)):
    __values__ = None
    __changes__ = None
    __fields__ = None
    __aliases__ = None

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
        for key, val in self.__values__.items():
            val = self.__fields__[key].flatten(val)
            data[key] = val

        return data

    def jsonify(self):
        """
        Return a dictionary suitable for JSON encoding.
        """
        data = {}
        for key, val in self.__values__.items():
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
        if isinstance(key, string_types):
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
        Allows dot notation.
        """
        if hasattr(values, '__values__'):
            for key, val in values.__values__.items():
                try:
                    self[key] = val
                except KeyError:
                    pass
        else:
            for key, val in values.items():
                try:
                    self[key] = val
                except KeyError:
                    pass

    def _get_field_path(self, entity, target, path=None):
        """
        Use dot notation to get a field and all it's
        ancestory fields.
        """
        path = path or []
        if '.' in target:
            name, right = target.split('.', 1)
            soak = False
            if name.endswith('?'):
                # Targets like 'child?.key' use "soak" to allow `child` to be empty
                name = name[:-1]
                soak = True

            field = entity.__fields__[name]
            key = '.'.join([f[0] for f in path] + [name])

            if isinstance(field, fields.EntityField):
                path.append((key, name, field, soak))
                return self._get_field_path(field.type, right, path)
            else:
                raise KeyError('Expected EntityField for %s' % key)
        else:
            soak = False
            if target.endswith('?'):
                # Targets like 'child?.key' use "soak" to allow `child` to be empty
                target = target[:-1]
                soak = True

            key = '.'.join([f[0] for f in path] + [target])
            path.append((key, target, entity.__fields__[target], soak))
            return path

    def __setattr__(self, name, value):
        """
        Don't allow setting attributes that haven't been defined as fields.
        """
        if name in self.__fields__:
            object.__setattr__(self, name, value)
        else:
            raise AttributeError('Field %r not defined.' % name)

    # Dict interface
    def __getitem__(self, name):
        try:
            if '.' in name:
                pos = self
                path = self._get_field_path(self, name)
                last = path[-1]
                path = path[:-1]
                for field_key, field_name, field, soak in path:
                    if isinstance(field, fields.EntityField):
                        if not getattr(pos, field_name):
                            if soak:
                                return Empty
                            else:
                                raise ValueError('%s is empty' % field_key)
                        pos = getattr(pos, field_name)
                    else:
                        raise ValueError('Expected Entity for %s' % field_key)

                # This should be the end of our path, just get it
                return getattr(pos, last[1])

            return getattr(self, name)
        except AttributeError:
            pass
        raise KeyError(name)

    def __setitem__(self, name, value):
        try:
            if '.' in name:
                pos = self
                path = self._get_field_path(self, name)
                last = path[-1]
                path = path[:-1]

                for field_key, field_name, field, soak in path:
                    if isinstance(field, fields.EntityField):
                        if not getattr(pos, field_name):
                            # Create a new Entity instance
                            setattr(pos, field_name, field.type())
                        pos = getattr(pos, field_name)
                    else:
                        raise ValueError('Expected Entity for %s' % field_key)

                # This should be the end of our path, just set it
                return setattr(pos, last[1], value)

            return setattr(self, name, value)
        except AttributeError:
            pass
        raise KeyError(name)

    def __delitem__(self, name):
        if name in self.__fields__:
            del self.__values__[name]
        else:
            raise KeyError('Field %r not defined.' % name)

    def __contains__(self, name):
        return name in self.__values__

    def __len__(self):
        return len(self.__values__)

    def iteritems(self):
        return self.__values__.items()

    def items(self):
        return self.__values__.items()

    def clear(self):
        return self.__values__.clear()

    def __iter__(self):
        return iter(self.__values__)

    @classmethod
    def adapt(cls, obj):
        return adapt(obj, cls)

    @classmethod
    def adapt_all(cls, obj):
        return (adapt(i, cls) for i in obj)

    def __repr__(self):
        return u'<%s %s>' % (self.__class__.__name__, json.dumps(dict(((k, text_type(v)) for k, v in self.__values__.items()))).replace('"', ''))

    def __getstate__(self):
        """Pickle state"""
        return {
            '__values__' : self.__values__,
            '__changes__': self.__changes__
        }

    def __setstate__(self, data):
        """Restore Pickle state"""
        object.__setattr__(self, '__values__', data['__values__'])
        object.__setattr__(self, '__changes__', data['__changes__'])

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.__values__ == other.__values__

    def __hash__(self):
        return id(self)

    def __neq__(self, other):
        return not self.__eq__(other)


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
        for key, val in values.items():
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
            for k, v in val.items():
                data[k] = self._flatten_value(v)
            val = data
        elif not isinstance(val, (float,) + integer_types + string_types):
            val = text_type(val)
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
            for k, v in val.items():
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
        for key, val in self.__values__.items():
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
        for key, val in self.__values__.items():
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


