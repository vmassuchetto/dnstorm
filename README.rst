About
-----

DNStorm is a Django project created as a MSc. project in Nuclear Technology by
Vinicius Massuchetto and Willy Hoppe de Sousa in decision-making theory.

The collaborative platform allows managers to state problems and ask help of
users that can contribute with quantified ideas to build a [strategy
table](http://www.structureddecisionmaking.org/tools/toolsstrategytables/).

Complete documentation can be found at [Read the
Docs](http://dnstorm.readthedocs.org/en/latest/).

A [live demo](http://dnstorm.herokuapp.com/) and experimental environment can
be found on Heroku.

Status
------

The development status is in its alpha stages.

Start a development instance
----------------------------

Clone the repository and go the project's root to build the environment:

::

    git clone git@github.com:vmassuchetto/dnstorm.git
    cd dnstorm

Start a virtual environment, load it and install the required packages from the
``requirements.txt`` file:

::

    virtualenv --distribute env
    source env/bin/activate
    pip install -r requirements.txt

Setup the SQLite3 database:

::

    python manage.py syncdb
    python manage.py migrate

Run your server:

::

    python manage.py runserver

The application might be running at ``http://localhost:8000``.


Localization
------------

The PO and MO files for each language are located in
``dnstorm/app/locale/<locale_code>/LC_MESSAGES``. To generate a PO file for a
given [locale code](http://stackoverflow.com/a/3191729/513401) run this:

::

    source env/bin/activate
    cd dnstorm/app/
    python ../../manage.py makemessages -l <locale code>


Documentation
-------------

To generate the Sphinx documentation files:

::

    source env/bin/activate
    cd docs
    make <documentation format>

Usually you might want to replace ``<documentation format>`` with ``html``.
