About
-----

DNStorm is an experiment in decision-making theory made by Vinicius Massuchetto
and Willy Hoppe de Sousa for the Master Program in Nuclear Technology
Applications of the Institute of Energy and Nuclear Research and University of
São Paulo in Brazil. The collaborative platform allows managers to state
problems and ask help of users that can contribute with quantified ideas to
build a `strategy table
<http://www.structureddecisionmaking.org/tools/toolsstrategytables/>`_.

The `project's fancy page <http://vmassuchetto.github.io/dnstorm>`_ presents
the software in a non-technical language.

Sphinx documentation can be found at `Read the Docs
<http://dnstorm.readthedocs.org/en/latest/>`_. A `live demo and experimental
environment <http://dnstorm.herokuapp.com/>`_ can be found on Heroku.


Status
------

The development status is in its alpha stages. Feel free to help by reporting
bugs and suggesting modifications on the `Github issues
<https://github.com/vmassuchetto/dnstorm/issues>`_.


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


Styles
------

The project's CSS is written in Sass using Compass. Make sure you have Ruby
with Gem to install it:

::

    gem install compass

With ``compass`` command available you can build the project's CSS:

::

    cd dnstorm/app/styles
    compass build

If you're developing the styles just run the compiler daemon to automatically
build when you change the ``dnstorm/app/styles/app.scss`` file.

::

    compass watch


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
