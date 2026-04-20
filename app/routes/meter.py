from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import Meter
from ..extensions import db

meter_bp = Blueprint('meter', __name__)

@meter_bp.route('/meter', methods=['GET'])
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

@meter_bp.route('/meter/<number>', methods=['GET'])
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

@meter_bp.route('/meter/connect', methods=['POST'])
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

@meter_bp.route('/meter/unlink', methods=['POST'])
@jwt_required()
def unlink_meter():
    user_id = get_jwt_identity()
    meter = Meter.query.filter_by(user_id=user_id).first()
    if not meter:
        return jsonify(message="No meter connected"), 404
    
    meter.user_id = None
    db.session.commit()
    return jsonify(message="Meter unlinked successfully"), 200
