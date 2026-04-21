import os
from datetime import timedelta
from flask import Flask
from .extensions import db, jwt, cors
from .routes.auth import auth_bp
from .routes.meter import meter_bp
from .routes.transactions import transactions_bp
from .routes.admin import admin_bp
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
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    with app.app_context():
        db.create_all()
        
        from .models import User
        from werkzeug.security import generate_password_hash
        admin_id = "admin@ecompteur.com"
        if not User.query.filter_by(identifier=admin_id).first():
            admin = User(
                name="Admin Sandra",
                identifier=admin_id,
                password=generate_password_hash("Admin123!"),
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()
            print(">>> Auto-seeded Admin User: " + admin_id)
        
    return app
