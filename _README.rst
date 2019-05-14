===========
SpringField
===========

.. image:: https://secure.travis-ci.org/plynth/springfield.png
    :target: http://travis-ci.org/plynth/springfield
    :alt: Build Status

SpringField makes API data easy.

SpringField makes it simple to model structured data. Once the data is
modeled, SpringField can parse API responses into easy to use Python objects
and types. It can also generate the same structured data for making API
request.

SpringField is ideal for:

- Restful JSON API data structures
- Parsing CSV data structures from ``csv.DictReader``
- Turning anything Python can parse into a ``dict`` or ``list`` into a
  structured object

There is also a helper library for using SpringField with Mongo: `springfield-
mongo <https://github.com/six8/springfield-mongo>`_


Quickstart
----------

To define an ``springfield.Entity``, subclass
``springfield.Entity``. Define your attributes by specifying
``fields``. This library provides the follow self-describing fields to
start with:

- ``IntField``
- ``FloatField``
- ``BooleanField``
- ``StringField``
- ``BytesField``
- ``DateTimeField``
- ``EmailField``
- ``UrlField``
- ``EntityField``
- ``CollectionField``


A quick example:


::

    #!/usr/bin/env python
    from springfield import Entity, fields
    from springfield.timeutil import utcnow


    class Bookmark(Entity):
        uri = fields.UrlField(doc='The bookmark uri.')
        verified = fields.BooleanField(doc='Whether or not this bookmark URI has been verified to exist.')
        added = fields.DateTimeField()


    class User(Entity):
        id = fields.IntField(doc='Auto-incremented database id.')
        email = fields.EmailField(doc='The user\'s email address.')
        bookmarks = fields.CollectionField(fields.EntityField(Bookmark))
        created = fields.DateTimeField()


    if __name__ == '__main__':
        user = User()
        user.id = 5
        user.email = 'foobar@example.com'
        user.bookmarks = [
            {'uri': 'https://github.com'},
            {'uri': 'ftp://google.com', 'verified': True}
        ]
        user.created = utcnow()
        data = user.to_json()
        # `data` is suitable to return in something like a JSON API.
        print data

        # Similarly, `data` can be adapted from a JSON API request body.
        user = User.from_json(data)
        print user.email
        print user.created
        print user.bookmarks


Will print (the json was prettified to protect the innocent):

::

    {
        "bookmarks":[
            {
                "uri":"https://github.com"
            },
            {
                "uri":"ftp://google.com",
                "verified":true
            }
        ],
        "created":"2017-01-25T20:25:54Z",
        "email":"foobar@example.com",
        "id":5
    }
    foobar@example.com
    2017-01-25 20:47:37+00:00
    [<Bookmark {uri: https://github.com}>, <Bookmark {verified: True, uri: ftp://google.com}>]


Notice a few things:

- Not every field is required for an entity. This is useful for doing sparse
  updates on an API.
- SpringField will adapt types in a non-destructive way.
- You can also create entities by adapting JSON, which is really handy at API
  boundaries.


Field Validation
----------------

SpringField does field validation when constructing entities, according to the
types defined by the fields on that entity. For example:

..
    >>> from springfield import Entity, fields
    >>>
    >>> class Foo(Entity):
    ...     bar = fields.IntField()
    ...
    >>> x = Foo()
    >>> x.bar = 'baz'
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/Users/jongartman/dev/personal/springfield/src/springfield/entity.py", line 201, in __setattr__
        object.__setattr__(self, name, value)
      File "/Users/jongartman/dev/personal/springfield/src/springfield/fields.py", line 40, in __set__
        new_value = self.field.set(instance, self.name, value)
      File "/Users/jongartman/dev/personal/springfield/src/springfield/fields.py", line 87, in set
        instance.__values__[name] = self.adapt(value)
      File "/Users/jongartman/dev/personal/springfield/src/springfield/fields.py", line 199, in adapt
        return int(value)
    ValueError: invalid literal for int() with base 10: 'baz'


You can define more complex field adaptation behavior by subclassing
``springfield.fields.Field`` and implementing your own fields. See
the documentation on ``springfield.fields.Field`` for more
information.

Similar Projects
----------------

* `schematics (formerly dictshield) <https://github.com/j2labs/schematics>`_
* `attrs <https://github.com/hynek/attrs>`_


Building Documentation
----------------------

To build documentation, first install the requirements:

..
    cd docs/
    pip install -r requirements.txt


Now you can build requirements with ``make``:

..
    make html


Running Tests
-------------

To run tests, first install the test requirements:

    pip install -r test_requirements.txt


Tests can be run with ./src/tests/runtests.py:

    python src/tests/runtests.py


.. include:: CHANGELOG.rst    
