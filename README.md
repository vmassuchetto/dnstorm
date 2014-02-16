All the command lines here require the virtualenv to be loaded:

    source env/bin/activate

## Development

Run the project in development mode:

    export DEBUG=True
    export DATABASE_DEBUG=True
    export STATICFILES_DEBUG=True
    export DEBUG_TOOLBAR=True
    python manage.py runserver

## Heroku deploy

Set `DEBUG` mode in Heroku:

    heroku config:set DEBUG=True

## Localization

To generate a PO file for a [locale
code](http://stackoverflow.com/a/3191729/513401):

    cd dnstorm/app/
    python ../../manage.py makemessages -l <locale code>
