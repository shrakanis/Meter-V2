from pathlib import Path


class Config:

    BASE_DIR = Path(__file__).resolve().parent

    DATA_DIR = BASE_DIR / "data"

    DATABASE = DATA_DIR / "energy.db"

    SECRET_KEY = "ChangeMe"

    DEBUG = True

    # Modbus
    MODBUS_SCAN_INTERVAL = 1.0

    MODBUS_TIMEOUT = 1.0

    MODBUS_RETRIES = 3

    MODBUS_SCAN_INTERVAL = 1.0

    # InfluxDB
    INFLUX_URL = "http://localhost:8086"
    INFLUX_TOKEN = ""
    INFLUX_ORG = "EnergyMonitor"
    INFLUX_BUCKET = "energy"

    # Web
    HOST = "0.0.0.0"
    PORT = 5000