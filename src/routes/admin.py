from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import User, Meter, Transaction, Setting
from ..extensions import db
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__)

def admin_required(fn):
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify(message="Admin access required"), 403
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper

@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    total_users = User.query.count()
    connected_meters = Meter.query.count()
    
    total_consumption = db.session.query(func.sum(Meter.balance)).scalar() or 0.0
    
    total_revenue = db.session.query(func.sum(Transaction.amount)).filter(Transaction.type == 'RECHARGE').scalar() or 0.0
    
    recent_txs = Transaction.query.order_by(Transaction.timestamp.desc()).limit(5).all()
    
    anomalies = Meter.query.filter(Meter.status != 'ACTIVE').count()
    
    return jsonify({
        "kpis": {
            "total_users": total_users,
            "meters_connected": connected_meters,
            "total_consumption": round(total_consumption, 2),
            "total_revenue": round(total_revenue, 2),
            "anomalies": anomalies,
            "pending_txs": 0 
        }
    })

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    users = User.query.all()
    return jsonify([{
        "id": u.id,
        "name": u.name,
        "identifier": u.identifier,
        "role": u.role
    } for u in users])

@admin_bp.route('/meters', methods=['GET'])
@admin_required
def get_meters():
    meters = db.session.query(Meter, User).outerjoin(User, Meter.user_id == User.id).all()
    return jsonify([{
        "id": m.Meter.id,
        "number": m.Meter.number,
        "balance": m.Meter.balance,
        "status": m.Meter.status,
        "user_name": m.User.name if m.User else "Non lié"
    } for m in meters])

@admin_bp.route('/transactions', methods=['GET'])
@admin_required
def get_transactions():
    txs = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    
    price_setting = Setting.query.filter_by(key='price_per_kwh').first()
    price_per_kwh = float(price_setting.value) if price_setting else 100.0
    
    result = []
    for t in txs:
        meter = Meter.query.get(t.meter_id)
        user = User.query.get(meter.user_id) if meter else None
        
        if t.type == 'RECHARGE':
            kwh = round(t.amount / price_per_kwh, 2)
            amount_fcfa = t.amount
        else:
            kwh = t.amount
            amount_fcfa = round(t.amount * price_per_kwh, 2)

        result.append({
            "id": t.id,
            "meter_number": meter.number if meter else "N/A",
            "user_name": user.name if user else "Inconnu",
            "amount": amount_fcfa,
            "kwh": kwh,
            "type": t.type,
            "timestamp": t.timestamp.isoformat()
        })
    return jsonify(result)

@admin_bp.route('/settings', methods=['GET'])
@admin_required
def get_settings():
    settings = Setting.query.all()
    if not settings:
        default_price = Setting(key='price_per_kwh', value='100', description='Prix du kiloWatt heure (FCFA)')
        db.session.add(default_price)
        db.session.commit()
        settings = [default_price]
    return jsonify({s.key: {"value": s.value, "description": s.description} for s in settings})

@admin_bp.route('/settings', methods=['POST'])
@admin_required
def update_settings():
    from flask import request
    data = request.json
    for key, val in data.items():
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value = str(val)
        else:
            setting = Setting(key=key, value=str(val))
            db.session.add(setting)
    db.session.commit()
    return jsonify(message="Settings updated successfully"), 200

@admin_bp.route('/alerts', methods=['GET'])
@admin_required
def get_alerts():
    
    anomalous_meters = Meter.query.filter(Meter.balance < 0).all()
    alerts = []
    for m in anomalous_meters:
        alerts.append({
            "id": f"alert-{m.id}",
            "type": "CRITICAL",
            "message": f"Balance négative détectée sur le compteur {m.number}",
            "meter_number": m.number,
            "timestamp": "2026-04-21T00:00:00" 
        })
    
    alerts.append({
        "id": "fraud-99",
        "type": "FRAUD",
        "message": "Tentative de contournement logiciel détectée",
        "meter_number": "CM-2024-001",
        "timestamp": "2026-04-21T01:30:00"
    })
    
    return jsonify(alerts)

@admin_bp.route('/analytics', methods=['GET'])
@admin_required
def get_analytics():
    return jsonify({
        "consumption": [30, 40, 35, 50, 49, 60, 70, 91, 125, 100, 110, 120],
        "revenue": [400000, 450000, 300000, 500000, 600000, 550000],
        "labels": ["Jan", "Fev", "Mar", "Avr", "Mai", "Juin", "Juil", "Aou", "Sep", "Oct", "Nov", "Dec"]
    })
