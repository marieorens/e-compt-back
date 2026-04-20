from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Meter, Transaction
from ..extensions import db

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/recharge', methods=['POST'])
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

@transactions_bp.route('/transfer', methods=['POST'])
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

@transactions_bp.route('/transactions', methods=['GET'])
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
