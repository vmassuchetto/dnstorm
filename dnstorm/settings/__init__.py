import os

if os.path.isfile(os.path.dirname(__file__) + '/heroku.py'):
    from heroku import *
else:
    from development import *
