Development
===========

It is recommended to run the following commands in a Docker container::

	docker run -it --rm -v "$PWD:$PWD" -w "$PWD" --entrypoint /bin/bash python:3

Building
--------

To build::

	make

The modified files should be committed.


Publish
-------

Publish to pypi::

	make publish


Documentation
-------------

To build documentation::

    make docs


Running Tests
-------------

To run tests::

	make test