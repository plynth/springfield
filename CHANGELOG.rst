---------
Changelog
---------

0.9.1
=====

* Fixed `Entity.get()` for Python 3

0.9.0
=====

* Switched from `future` to `six` Python 2/3 compatibility libraries because `future`'s 
  modified `str` does not play well with adapters.

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

* Allow empty values for URL