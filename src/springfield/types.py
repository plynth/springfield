class EmptyType(type):
    """
    Acts like ``None`` but is used when a value is explicitly left empty.
    """
    def __new__(cls, name, bases, dct):
        return type.__new__(cls, name, bases, dct)
    def __init__(cls, name, bases, dct):
        super(EmptyType, cls).__init__(name, bases, dct)
    def __str__(self):
        return ""
    def __repr__(self):
        return "Empty"
    def __nonzero__(self):
        return False
    def __len__(self):
        return 0
    def __call__(self, *args, **kwargs):
        return None
    def __contains__(self, item):
        return False
    def __iter__(self):
        return self
    def next(*args):
        raise StopIteration

#: A value that is explicitly empty
Empty = EmptyType("Empty", (type,), {})