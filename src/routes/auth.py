from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import User
from ..extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.json
    if User.query.filter_by(identifier=data['identifier']).first():
        return jsonify(message="User already exists"), 400
    
    hashed_pw = generate_password_hash(data['password'])
    new_user = User(name=data['name'], identifier=data['identifier'], password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify(message="User created"), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(identifier=data['identifier']).first()
    
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify(message="Invalid credentials"), 401
    
    access_token = create_access_token(identity=str(user.id))
    return jsonify(token=access_token, role=user.role), 200
