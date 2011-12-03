from datetime import datetime

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

class EmailField(StringField):
    """
    Field that validates as an email address.
    """
    
class UrlField(StringField):
    pass     

class EntityField(AdaptableTypeField):
    def __init__(self, entity, *args, **kwargs):
        self.type = entity
        super(EntityField, self).__init__(*args, **kwargs)        

    def flatten(self, value):
        return value.flatten()

class IdField(Field):
    pass    

class CollectionField(Field):
    def __init__(self, field, *args, **kwargs):
        self.field = field
        super(CollectionField, self).__init__(*args, **kwargs)

    def adapt(self, obj):
        values = []
        for item in obj:
            values.append(self.field.adapt(item))
        return values

    def flatten(self, value):
        values = []
        for item in value:
            values.append(self.field.flatten(item))

        return values