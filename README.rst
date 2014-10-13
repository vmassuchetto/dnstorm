.. image:: https://travis-ci.org/vmassuchetto/dnstorm.svg?branch=master
    :target: https://travis-ci.org/vmassuchetto/dnstorm

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


Project URL
-----------

Change the project URL while in development or production by changing the URL
in `sites framework
<https://docs.djangoproject.com/en/1.5/ref/contrib/sites/>`_.

::

    python manage.py shell
    from django.contrib.sites.models import Site
    s = Site.objects.get(id=1)
    s.domain = '<your domain>'
    s.save()


CSS
---

The project's CSS is written in SCSS using `Sass <http://sass-lang.com>`_,
`Compass <http://compass-style.org>`_ and `django-bower
<https://github.com/nvbn/django-bower>`_. Make sure you have Ruby with Gem to
install it:

::

    gem install compass
    python manage.py bower install

And then, to generate the static files:

::

    cd dnstorm/app/static/scss
    compass compile

If you're developing, you might want to use ``compass watch`` instead.


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


Graphviz
--------

You'll need Graphviz if you want to generate the system's UML model
representation:

::

    apt-get install graphviz graphviz-dev pkg-config
    pip install -r requirements.txt

And to generate the thing:

::

    python manage.py graph_models -a -g -o project.png

