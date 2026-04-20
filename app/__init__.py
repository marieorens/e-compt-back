import os
from datetime import timedelta
from flask import Flask
from .extensions import db, jwt, cors
from .routes.auth import auth_bp
from .routes.meter import meter_bp
from .routes.transactions import transactions_bp
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///ecompteur.db')
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)
        
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-fallback')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app)
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(meter_bp)
    app.register_blueprint(transactions_bp)
    
    with app.app_context():
        db.create_all()
        
    return app
