from app import create_app
from src.extensions import db
from src.models import User
from werkzeug.security import generate_password_hash

app = create_app()

def seed_admin():
    with app.app_context():
        admin_identifier = "admin@ecompteur.com"
        admin = User.query.filter_by(identifier=admin_identifier).first()
        
        if not admin:
            hashed_pw = generate_password_hash("Admin123!")
            admin = User(
                name="Admin Sandra",
                identifier=admin_identifier,
                password=hashed_pw,
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user {admin_identifier} created with password 'Admin123!'")
        else:
            admin.role = "admin"
            db.session.commit()
            print(f"User {admin_identifier} is now an admin")

if __name__ == '__main__':
    seed_admin()
