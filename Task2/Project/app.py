from flask import Flask, request, jsonify
from models import db, Zone, Device, SensorType, Measurement
from datetime import datetime
from flasgger import Swagger

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://postgres:170787@localhost:5432/postgres"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

swagger = Swagger(app, template={
    "swagger": "2.0",
    "info": {
        "title": "Air Quality Monitoring API",
        "description": "REST API для серверної частини системи моніторингу якості повітря (ЛР2).",
        "version": "1.0.0"
    },
    "basePath": "/",
    "schemes": ["http"],
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "tags": [
        {"name": "System", "description": "Системні ендпоінти"},
        {"name": "Zones", "description": "Зони моніторингу"},
        {"name": "Devices", "description": "IoT-пристрої"},
        {"name": "SensorTypes", "description": "Типи сенсорів (довідник)"},
        {"name": "Measurements", "description": "Вимірювання"}
    ]
})


def error_response(message: str, status: int = 400):
    return jsonify({"error": message}), status


@app.get("/health")
def health():
    """
    Перевірка працездатності сервера
    ---
    tags:
      - System
    responses:
      200:
        description: Сервер працює
        schema:
          type: object
          properties:
            status:
              type: string
              example: ok
    """
    return {"status": "ok"}

# Zones
@app.get("/api/zones")
def list_zones():
    """
    Отримати список зон моніторингу
    ---
    tags:
      - Zones
    responses:
      200:
        description: Список зон
        schema:
          type: array
          items:
            type: object
            properties:
              zone_id: {type: integer, example: 1}
              zone_name: {type: string, example: "Центр"}
              region: {type: string, example: "Харків"}
              latitude: {type: number, example: 49.9935}
              longitude: {type: number, example: 36.230383}
    """
    zones = Zone.query.order_by(Zone.zone_id).all()
    return jsonify([{
        "zone_id": z.zone_id,
        "zone_name": z.zone_name,
        "region": z.region,
        "latitude": float(z.latitude),
        "longitude": float(z.longitude)
    } for z in zones])


@app.post("/api/zones")
def create_zone():
    """
    Створити нову зону моніторингу
    ---
    tags:
      - Zones
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [zone_name, region, latitude, longitude]
          properties:
            zone_name: {type: string, example: "Центр"}
            region: {type: string, example: "Харків"}
            latitude: {type: number, example: 49.9935}
            longitude: {type: number, example: 36.230383}
    responses:
      201:
        description: Зону створено
        schema:
          type: object
          properties:
            zone_id: {type: integer, example: 1}
      400:
        description: Некоректні дані
    """
    data = request.get_json(force=True)
    try:
        z = Zone(
            zone_name=data["zone_name"],
            region=data["region"],
            latitude=data["latitude"],
            longitude=data["longitude"]
        )
        db.session.add(z)
        db.session.commit()
        return jsonify({"zone_id": z.zone_id}), 201
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 400)

# Devices (GET/POST/PUT/DELETE)
@app.get("/api/devices")
def list_devices():
    """
    Отримати список IoT-пристроїв (опційно з фільтром по зоні)
    ---
    tags:
      - Devices
    parameters:
      - in: query
        name: zone_id
        type: integer
        required: false
        description: Фільтр пристроїв за ідентифікатором зони
        example: 1
    responses:
      200:
        description: Список пристроїв
        schema:
          type: array
          items:
            type: object
            properties:
              device_id: {type: integer, example: 1}
              serial_number: {type: string, example: "DEV-0001"}
              zone_id: {type: integer, example: 1}
              status: {type: string, example: "ONLINE"}
              last_seen_at: {type: string, example: "2026-01-12T18:10:00+00:00"}
    """
    zone_id = request.args.get("zone_id", type=int)
    q = Device.query
    if zone_id:
        q = q.filter(Device.zone_id == zone_id)
    devices = q.order_by(Device.device_id).all()
    return jsonify([{
        "device_id": d.device_id,
        "serial_number": d.serial_number,
        "zone_id": d.zone_id,
        "status": d.status,
        "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None
    } for d in devices])


@app.post("/api/devices")
def create_device():
    """
    Створити IoT-пристрій
    ---
    tags:
      - Devices
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [serial_number, zone_id]
          properties:
            serial_number: {type: string, example: "DEV-0003"}
            zone_id: {type: integer, example: 1}
            status: {type: string, example: "OFFLINE"}
            last_seen_at:
              type: string
              description: "ISO 8601 datetime (optional)"
              example: "2026-01-12T12:00:00Z"
    responses:
      201:
        description: Пристрій створено
        schema:
          type: object
          properties:
            device_id: {type: integer, example: 1}
      400:
        description: Некоректні дані
    """
    data = request.get_json(force=True)
    try:
        last_seen = None
        if data.get("last_seen_at"):
            last_seen = datetime.fromisoformat(data["last_seen_at"].replace("Z", "+00:00"))

        d = Device(
            serial_number=data["serial_number"],
            zone_id=data["zone_id"],
            status=data.get("status", "OFFLINE"),
            last_seen_at=last_seen
        )
        db.session.add(d)
        db.session.commit()
        return jsonify({"device_id": d.device_id}), 201
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 400)


@app.put("/api/devices/<int:device_id>")
def update_device(device_id: int):
    """
    Оновити дані пристрою
    ---
    tags:
      - Devices
    parameters:
      - in: path
        name: device_id
        required: true
        type: integer
        example: 1
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            serial_number: {type: string, example: "DEV-0001"}
            zone_id: {type: integer, example: 2}
            status: {type: string, example: "ONLINE"}
            last_seen_at:
              type: string
              example: "2026-01-12T12:30:00Z"
    responses:
      200:
        description: Пристрій оновлено
        schema:
          type: object
          properties:
            device_id: {type: integer, example: 1}
            updated: {type: boolean, example: true}
      404:
        description: Пристрій не знайдено
    """
    data = request.get_json(force=True)
    d = Device.query.get(device_id)
    if not d:
        return error_response("Device not found", 404)

    try:
        if "serial_number" in data:
            d.serial_number = data["serial_number"]
        if "zone_id" in data:
            d.zone_id = data["zone_id"]
        if "status" in data:
            d.status = data["status"]
        if "last_seen_at" in data and data["last_seen_at"] is not None:
            d.last_seen_at = datetime.fromisoformat(data["last_seen_at"].replace("Z", "+00:00"))

        db.session.commit()
        return jsonify({"device_id": d.device_id, "updated": True})
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 400)


@app.delete("/api/devices/<int:device_id>")
def delete_device(device_id: int):
    """
    Видалити пристрій
    ---
    tags:
      - Devices
    parameters:
      - in: path
        name: device_id
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Пристрій видалено
        schema:
          type: object
          properties:
            deleted: {type: boolean, example: true}
      404:
        description: Пристрій не знайдено
    """
    d = Device.query.get(device_id)
    if not d:
        return error_response("Device not found", 404)

    try:
        db.session.delete(d)
        db.session.commit()
        return jsonify({"deleted": True})
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 400)


# Sensor Types (GET/POST/PUT/DELETE)
@app.get("/api/sensor-types")
def list_sensor_types():
    """
    Отримати список типів сенсорів
    ---
    tags:
      - SensorTypes
    responses:
      200:
        description: Список типів сенсорів
        schema:
          type: array
          items:
            type: object
            properties:
              sensor_type_id: {type: integer, example: 1}
              code: {type: string, example: "CO2"}
              sensor_name: {type: string, example: "Діоксид вуглецю"}
              unit: {type: string, example: "ppm"}
    """
    items = SensorType.query.order_by(SensorType.sensor_type_id).all()
    return jsonify([{
        "sensor_type_id": s.sensor_type_id,
        "code": s.code,
        "sensor_name": s.sensor_name,
        "unit": s.unit
    } for s in items])


@app.post("/api/sensor-types")
def create_sensor_type():
    """
    Створити тип сенсора
    ---
    tags:
      - SensorTypes
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [code, sensor_name, unit]
          properties:
            code: {type: string, example: "CO2"}
            sensor_name: {type: string, example: "Діоксид вуглецю"}
            unit: {type: string, example: "ppm"}
    responses:
      201:
        description: Тип сенсора створено
        schema:
          type: object
          properties:
            sensor_type_id: {type: integer, example: 1}
    """
    data = request.get_json(force=True)
    try:
        s = SensorType(code=data["code"], sensor_name=data["sensor_name"], unit=data["unit"])
        db.session.add(s)
        db.session.commit()
        return jsonify({"sensor_type_id": s.sensor_type_id}), 201
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 400)


@app.put("/api/sensor-types/<int:sensor_type_id>")
def update_sensor_type(sensor_type_id: int):
    """
    Оновити тип сенсора
    ---
    tags:
      - SensorTypes
    parameters:
      - in: path
        name: sensor_type_id
        required: true
        type: integer
        example: 1
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            code: {type: string, example: "CO2"}
            sensor_name: {type: string, example: "Діоксид вуглецю"}
            unit: {type: string, example: "ppm"}
    responses:
      200:
        description: Тип сенсора оновлено
        schema:
          type: object
          properties:
            sensor_type_id: {type: integer, example: 1}
            updated: {type: boolean, example: true}
      404:
        description: Тип сенсора не знайдено
    """
    data = request.get_json(force=True)
    s = SensorType.query.get(sensor_type_id)
    if not s:
        return error_response("Sensor type not found", 404)

    try:
        if "code" in data:
            s.code = data["code"]
        if "sensor_name" in data:
            s.sensor_name = data["sensor_name"]
        if "unit" in data:
            s.unit = data["unit"]

        db.session.commit()
        return jsonify({"sensor_type_id": s.sensor_type_id, "updated": True})
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 400)


@app.delete("/api/sensor-types/<int:sensor_type_id>")
def delete_sensor_type(sensor_type_id: int):
    """
    Видалити тип сенсора
    ---
    tags:
      - SensorTypes
    parameters:
      - in: path
        name: sensor_type_id
        required: true
        type: integer
        example: 1
    responses:
      200:
        description: Тип сенсора видалено
        schema:
          type: object
          properties:
            deleted: {type: boolean, example: true}
      404:
        description: Тип сенсора не знайдено
    """
    s = SensorType.query.get(sensor_type_id)
    if not s:
        return error_response("Sensor type not found", 404)

    try:
        db.session.delete(s)
        db.session.commit()
        return jsonify({"deleted": True})
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 400)

# Measurements (GET/POST)
@app.post("/api/measurements")
def create_measurement():
    """
    Додати вимірювання (надсилає IoT-пристрій або клієнт)
    ---
    tags:
      - Measurements
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [device_id, sensor_type_id, value, measured_at]
          properties:
            device_id: {type: integer, example: 1}
            sensor_type_id: {type: integer, example: 1}
            value: {type: number, example: 22.7}
            measured_at:
              type: string
              description: "ISO 8601 datetime (наприклад, 2026-01-12T12:00:00Z)"
              example: "2026-01-12T12:00:00Z"
            quality_flag:
              type: string
              description: "OK / SUSPECT / ERROR"
              example: "OK"
    responses:
      201:
        description: Вимірювання додано
        schema:
          type: object
          properties:
            measurement_id: {type: integer, example: 1}
    """
    data = request.get_json(force=True)
    try:
        measured_at = datetime.fromisoformat(data["measured_at"].replace("Z", "+00:00"))

        m = Measurement(
            device_id=data["device_id"],
            sensor_type_id=data["sensor_type_id"],
            value=data["value"],
            measured_at=measured_at,
            quality_flag=data.get("quality_flag", "OK")
        )
        db.session.add(m)
        db.session.commit()
        return jsonify({"measurement_id": int(m.measurement_id)}), 201
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 400)


@app.get("/api/measurements")
def get_measurements():
    """
    Отримати список вимірювань з фільтрами
    ---
    tags:
      - Measurements
    parameters:
      - in: query
        name: device_id
        type: integer
        required: false
        description: Фільтр за пристроєм
        example: 1
      - in: query
        name: sensor_type_id
        type: integer
        required: false
        description: Фільтр за типом сенсора
        example: 1
      - in: query
        name: limit
        type: integer
        required: false
        description: Максимальна кількість записів (за замовчуванням 100)
        example: 100
    responses:
      200:
        description: Список вимірювань (відсортовано за часом спадання)
        schema:
          type: array
          items:
            type: object
            properties:
              measurement_id: {type: integer, example: 1}
              device_id: {type: integer, example: 1}
              sensor_type_id: {type: integer, example: 1}
              value: {type: number, example: 22.7}
              measured_at: {type: string, example: "2026-01-12T12:00:00+00:00"}
              received_at: {type: string, example: "2026-01-12T12:00:01+00:00"}
              quality_flag: {type: string, example: "OK"}
    """
    device_id = request.args.get("device_id", type=int)
    sensor_type_id = request.args.get("sensor_type_id", type=int)
    limit = request.args.get("limit", default=100, type=int)

    q = Measurement.query
    if device_id:
        q = q.filter(Measurement.device_id == device_id)
    if sensor_type_id:
        q = q.filter(Measurement.sensor_type_id == sensor_type_id)

    items = q.order_by(Measurement.measured_at.desc()).limit(limit).all()
    return jsonify([{
        "measurement_id": int(m.measurement_id),
        "device_id": m.device_id,
        "sensor_type_id": m.sensor_type_id,
        "value": float(m.value),
        "measured_at": m.measured_at.isoformat(),
        "received_at": m.received_at.isoformat(),
        "quality_flag": m.quality_flag
    } for m in items])


if __name__ == "__main__":
    app.run(debug=True)
