---------
Changelog
---------

0.8.0
=====

* Added support for Python 3.6+
* Dropped support for Python <2.7

0.7.17
======

* Fix packages for pytest plugin

0.7.16
======

* Allow EntityFields to use dotted-name class strings. This was done to allow circular references in entities that may refer to one another.
* Added BytesField

0.7.15
======

Bug Fixes
---------

* Allow empty values for URL