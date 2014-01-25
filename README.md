Run the project in development mode:

    export DEBUG=True
    export DATABASE_DEBUG=True
    source env/bin/activate
    python manage.py runserver

Set `DEBUG` mode in Heroku:

    heroku config:set DEBUG=True
