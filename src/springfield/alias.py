from springfield.fields import EntityField

class AliasDescriptor(object):
    """
    A descriptor that handles setting and getting :class:`Alias` values
    on an :class:`Entity`.
    """
    def __init__(self, name, alias):
        """
        :param name: The name of the :class:`Entity`'s attribute
        :param alias: A :class:`Alias` instance
        """
        self.name = name
        self.alias = alias
        self.__doc__ = self.alias.__doc__

    def __get__(self, instance, owner):
        """
        Get the :class:`Alias`'s value. 
        """
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
        """
        Set a value for this :class:`Alias`.
        """
        if value is Empty:
            if self.name in instance.__values__:
                del instance.__values__[self.name]
        else:
            instance.__values__[self.name] = self.field.adapt(value)
        instance.__changes__.add(self.name)

class Alias(object):
    """
    Maps its value to another field's value

    Map fields aren't serialized, they are just attribute accessors.
    """
    def __init__(self, target, doc=None, *args, **kwargs):
        """        
        :param target: The field value to target 
        :param doc: The docstring to assign to this alias and its descriptor
        """
        self.__doc__ = doc
        self.target = target

    def _get_value(self, entity, target):
        if '.' in target:
            root, right = target.split('.', 1)
            return self._get_value(entity[root], right)
        else:
            return entity[target]

    def _set_value(self, entity, target, value):
        if '.' in target:
            root, right = target.split('.', 1)
            return self._set_value(entity[root], right, value)
        else:
            entity[target] = value

    def _get_field(self, entity, target):
        if '.' in target:
            name, right = target.split('.', 1)
            field = entity.__fields__[name]
            if isinstance(field, EntityField):
                return self._get_field(field.type, right)
            else:
                raise KeyError('Unexpected field type for %s' % name)
        else:
            return entity.__fields__[target]

    def get(self, entity):
        return self._get_value(entity, self.target)

    def set(self, entity, value):
        self._set_value(entity, self.target, value)

    def init(self, cls):
        """
        Initialize the alias for its owner :class:`Entity` class. Any specialization
        that needs to be done based on the :class:`Entity` class itself should be done here.

        :param cls: An :class:`Entity` class.
        """

    def make_descriptor(self, name):
        """
        Create a descriptor for this :class:`Alias` to attach to
        an :class:`Entity`.
        """
        return AliasDescriptor(name=name, alias=self)