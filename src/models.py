from datetime import datetime
from .extensions import db

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
