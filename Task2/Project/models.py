from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint
from datetime import datetime

db = SQLAlchemy()

class Role(db.Model):
    __tablename__ = "roles"
    role_id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String(50), nullable=False, unique=True)

class User(db.Model):
    __tablename__ = "user"  # важливо: як у БД ("user")
    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.role_id"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

class Zone(db.Model):
    __tablename__ = "zones"
    zone_id = db.Column(db.Integer, primary_key=True)
    zone_name = db.Column(db.String(200), nullable=False)
    region = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Numeric(9, 6), nullable=False)
    longitude = db.Column(db.Numeric(9, 6), nullable=False)

    __table_args__ = (
        UniqueConstraint("region", "zone_name", name="ux_zones_region_name"),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="chk_zones_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="chk_zones_longitude"),
    )

class Device(db.Model):
    __tablename__ = "devices"
    device_id = db.Column(db.Integer, primary_key=True)
    serial_number = db.Column(db.String(100), nullable=False, unique=True)
    zone_id = db.Column(db.Integer, db.ForeignKey("zones.zone_id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="OFFLINE")
    last_seen_at = db.Column(db.DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("status IN ('ONLINE','OFFLINE')", name="chk_devices_status"),
    )

class SensorType(db.Model):
    __tablename__ = "sensor_types"
    sensor_type_id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False, unique=True)
    sensor_name = db.Column(db.String(200), nullable=False)
    unit = db.Column(db.String(50), nullable=False)

class Measurement(db.Model):
    __tablename__ = "measurements"
    measurement_id = db.Column(db.BigInteger, primary_key=True)
    sensor_type_id = db.Column(db.Integer, db.ForeignKey("sensor_types.sensor_type_id"), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.device_id"), nullable=False)
    value = db.Column(db.Numeric(14, 6), nullable=False)
    measured_at = db.Column(db.DateTime(timezone=True), nullable=False)
    received_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    quality_flag = db.Column(db.String(20), nullable=False, default="OK")

    __table_args__ = (
        CheckConstraint("quality_flag IN ('OK','SUSPECT','ERROR')", name="chk_measurements_quality"),
    )
