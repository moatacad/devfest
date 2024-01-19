from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate


csrf=CSRFProtect()
def create_app():
    '''This is an application factory used to avoid cyclic error'''
    from pkg.models import db
    from pkg import config
    
    app = Flask(__name__,template_folder='templates', static_folder='static',instance_relative_config=True)
    
    app.config.from_pyfile("config.py") #will load the config from instance folder
    app.config.from_object(config.TestConfig)
    db.init_app(app) 
    csrf.init_app(app)
    migrate = Migrate(app, db)

    return app

app = create_app()
from pkg import admin_routes,user_routes 