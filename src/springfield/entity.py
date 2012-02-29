import json
import inspect
from springfield.fields import Field, Empty

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

    def set(self, key, value):
        self.__setattr__(key, value)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def update(self, values):
        """
        Update attibutes. Ignore keys that aren't fields.
        """
        for key, val in values.iteritems():
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
        if obj is None:
            return obj
        elif isinstance(obj, cls):
            return obj

        e = cls()
        if isinstance(e, obj.__class__):
            # obj is an instance of the parent class, copy all attibutes you can
            object.__setattr__(e, '__values__', obj.__values__)
        elif isinstance(obj, dict):
            e.update(obj)
        elif hasattr(obj, '_fields'):
            if obj._fields:
                d = {}
                for attr_name, field in obj._fields.items():
                    d[attr_name] = getattr(obj, attr_name)
                e.update(d)
        elif '_data' in obj.__dict__:
            e.update(obj.__dict__['_data'])
        else:
            e.update(obj.__dict__)

        return e

    @classmethod
    def adapt_all(cls, obj):
        return (cls.adapt(i) for i in obj)

    @classmethod
    def __adapt__(cls, obj):
        return cls.adapt(obj)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, json.dumps(dict(((k, str(v)) for k, v in self.__values__.iteritems()))).replace('"', ''))

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
