.. image:: https://travis-ci.org/vmassuchetto/dnstorm.svg?branch=master
    :target: https://travis-ci.org/vmassuchetto/dnstorm

.. image:: https://readthedocs.org/projects/dnstorm/badge/?version=latest
    :target: https://readthedocs.org/projects/pip/badge/?version=latest

About
-----

`DNStorm <http://vmassuhetto.github.io/dnstorm>`_ is an experiment in
decision-making theory made by `Vinicius Massuchetto
<http://buscatextual.cnpq.br/buscatextual/visualizacv.do?metodo=apresentar&id=K4453533E8>`_
and `Willy Hoppe de Sousa
<http://buscatextual.cnpq.br/buscatextual/visualizacv.do?metodo=apresentar&id=K4751001U6>`_
for the Master Program in Nuclear Technology Applications of the `Institute of
Energy and Nuclear Research <http://ipen.br>`_ and `University of São Paulo
<http://usp.br>`_ in Brazil.

This is a simple collaborative platform that allows managers to state problems
and ask for contributions of quantified ideas from a web `brainstorming
<http://en.wikipedia.org/wiki/Brainstorming>`_ processes that will build the
problem and solution presentation in the format of a `strategy table
<http://www.structureddecisionmaking.org/tools/toolsstrategytables>`_.

The `project's fancy page <http://vmassuchetto.github.io/dnstorm>`_ presents
the software in a non-technical language. Sphinx documentation can be found at
`Read the Docs <http://dnstorm.readthedocs.org/en/latest/>`_. A `live demo and
experimental environment <http://dnstorm.herokuapp.com/>`_ can be found on
Heroku.


Status
------

The development status is in its alpha stages. Feel free to help by reporting
bugs and development suggestions on `Github issues
<https://github.com/vmassuchetto/dnstorm/issues>`_.

Build a test and development installation
-----------------------------------------

The project uses Python 2.7. Make sure your `python`, `virtualenv` and `pip`
binaries meets this version.

Clone the repository and go the project's root to build the environment:

::

    git clone git@github.com:vmassuchetto/dnstorm.git
    cd dnstorm

Start a virtual environment, load it and install the required packages from the
``requirements.txt`` file. After this, make sure all the command line used from
here is executed in this virtual environment (has the ``(env)`` on the command
prompt).

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


CSS
---

For hosting environment reasons, the compiled ``static/scss/app.css`` is
already in the project's repository. That means you don't need to go further if
you're not developing.

The project's CSS uses the `Foundation <http://foundation.zurb.com>_` framework
and is generated with `Sass <http://sass-lang.com>`_. DNStorm uses a set of
`Grunt <http://gruntjs.com>`_ and `Bower <http://bower.io>`_ packages for the
static files. To install everything via `nodejs`:

::

    npm install
    ./node_modules/bower/bin/bower install

And to generate the static CSS:

::

    ./node_modules/grunt-cli/bin/grunt build

If you're editing the main ``static/scss/app.scss`` file, you
might want to use ``grunt watch`` instead.


E-mails
-------

E-mail receival in development mode can be checked by a SMTP debugging server:

::

     python -m smtpd -n -c DebuggingServer localhost:1025


Localization
------------

The PO and MO files for each language are located in
``dnstorm/app/locale/<locale_code>/LC_MESSAGES``. To generate a PO file for a
given `locale code <http://stackoverflow.com/a/3191729/513401>`_ run this:

::

    source env/bin/activate
    cd dnstorm/app/
    python ../../manage.py makemessages -l <locale code>


Documentation
-------------

To generate the `Sphinx <http://sphinx-doc.org/>`_ documentation files:

::

    source env/bin/activate
    cd docs
    make <documentation format>

Usually you might want to replace ``<documentation format>`` with ``html``.


Deploying on Heroku
-------------------

In order to successfully deploy on Heroku this project needs the following
setup:

* ``package.json`` file must be deleted
* ``bower.json`` must be deleted
* ``dnstorm/app/static/components`` directory must be included
* ``dnstorm/settings/heroku.py`` file must be created accordingly to the sample
configuration file on ``dnstorm/settings/heroku-sample.py``

You can create another ``heroku`` branch to deploy to the ``heroku`` remote
like this:

::

    git push heroku heroku:master
