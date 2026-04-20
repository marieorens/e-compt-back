import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecompteur.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-fallback')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

db = SQLAlchemy(app)
jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    identifier = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Meter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(50), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    balance = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='ACTIVE')

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meter_id = db.Column(db.Integer, db.ForeignKey('meter.id'))
    amount = db.Column(db.Float)
    type = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    if User.query.filter_by(identifier=data['identifier']).first():
        return jsonify(message="User already exists"), 400
    
    hashed_pw = generate_password_hash(data['password'])
    new_user = User(name=data['name'], identifier=data['identifier'], password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify(message="User created"), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(identifier=data['identifier']).first()
    
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify(message="Invalid credentials"), 401
    
    access_token = create_access_token(identity=str(user.id))
    return jsonify(token=access_token), 200

@app.route('/meter', methods=['GET'])
@jwt_required()
def get_meter():
    user_id = get_jwt_identity()
    meter = Meter.query.filter_by(user_id=user_id).first()
    if not meter:
        return jsonify(message="No meter connected"), 404
    return jsonify({
        "number": meter.number,
        "balance": meter.balance,
        "status": meter.status
    })

@app.route('/meter/<number>', methods=['GET'])
@jwt_required()
def get_meter_by_number(number):
    meter = Meter.query.filter_by(number=number).first()
    if not meter:
        return jsonify(message="Meter not found"), 404
    
    return jsonify({
        "number": meter.number,
        "status": meter.status,
        "is_active": meter.status == 'ACTIVE'
    })

@app.route('/meter/connect', methods=['POST'])
@jwt_required()
def connect_meter():
    user_id = get_jwt_identity()
    data = request.json
    
    if not data or 'number' not in data:
        return jsonify(message="Meter number is required"), 400
        
    if Meter.query.filter_by(user_id=user_id).first():
        return jsonify(message="User already has a meter connected"), 400
        
    new_meter = Meter(number=data['number'], user_id=user_id, balance=18.7)
    db.session.add(new_meter)
    db.session.commit()
    return jsonify(message="Meter connected", balance=18.7), 201

@app.route('/meter/unlink', methods=['POST'])
@jwt_required()
def unlink_meter():
    user_id = get_jwt_identity()
    meter = Meter.query.filter_by(user_id=user_id).first()
    if not meter:
        return jsonify(message="No meter connected"), 404
    
    meter.user_id = None
    db.session.commit()
    return jsonify(message="Meter unlinked successfully"), 200

@app.route('/recharge', methods=['POST'])
@jwt_required()
def recharge():
    user_id = get_jwt_identity()
    data = request.json
    meter = Meter.query.filter_by(user_id=user_id).first()
    if not meter:
        return jsonify(message="Meter not found"), 404
    
    amount = data.get('amount', 0)
    if amount <= 0:
        return jsonify(message="Invalid amount"), 400
        
    kwh = amount / 100
    meter.balance += kwh
    
    tx = Transaction(meter_id=meter.id, amount=amount, type='RECHARGE')
    db.session.add(tx)
    db.session.commit()
    return jsonify(message="Recharge successful", new_balance=round(meter.balance, 2))

@app.route('/transfer', methods=['POST'])
@jwt_required()
def transfer():
    user_id = get_jwt_identity()
    data = request.json
    
    sender_meter = Meter.query.filter_by(user_id=user_id).first()
    if not sender_meter:
        return jsonify(message="You don't have a meter connected"), 404
        
    amount_kwh = float(data.get('amount', 0))
    target_number = data.get('target_meter')
    
    if amount_kwh <= 0:
        return jsonify(message="Invalid amount"), 400
        
    if sender_meter.balance < amount_kwh:
        return jsonify(message="Insufficient balance"), 400
        
    if sender_meter.number == target_number:
        return jsonify(message="Cannot transfer to the same meter"), 400

    
    target_meter = Meter.query.filter_by(number=target_number).first()
    
    sender_meter.balance -= amount_kwh
    if target_meter:
        target_meter.balance += amount_kwh
        
    tx = Transaction(meter_id=sender_meter.id, amount=amount_kwh, type='TRANSFER_OUT')
    db.session.add(tx)
    
    if target_meter:
        tx_in = Transaction(meter_id=target_meter.id, amount=amount_kwh, type='TRANSFER_IN')
        db.session.add(tx_in)
        
    db.session.commit()
    return jsonify(message="Transfer successful", new_balance=round(sender_meter.balance, 2))

@app.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    user_id = get_jwt_identity()
    meter = Meter.query.filter_by(user_id=user_id).first()
    if not meter:
        return jsonify([])
    
    transactions = Transaction.query.filter_by(meter_id=meter.id).order_by(Transaction.timestamp.desc()).all()
    return jsonify([{
        "id": tx.id,
        "amount": tx.amount,
        "type": tx.type,
        "timestamp": tx.timestamp.isoformat()
    } for tx in transactions])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
