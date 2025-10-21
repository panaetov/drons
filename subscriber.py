import datetime
import logging

import paho.mqtt.client as mqtt

import database


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')


def on_connect(client, userdata, flags, reason_code, properties=None):
    client.subscribe("beacon/detect", qos=1)


def on_message(_, __, msg):
    drone_id, lat, lon, beacon_id, tos, toa = msg.payload.decode().split(":")[:6]

    logger.info(f"Получено: {msg.topic} → {msg.payload.decode()}")
    database.BeaconDetection(
        beacon_id=beacon_id,
        saved_at=datetime.datetime.utcnow(),
        receiver_id=drone_id,
        receiver_lat=lat,
        receiver_lon=lon,
        toa=toa,
        tos=tos,
     ).save()


CLIENT = mqtt.Client(
    protocol=mqtt.MQTTv5,
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="subscriber",
)
CLIENT.on_message = on_message
CLIENT.on_connect = on_connect

CLIENT.connect("localhost", 1883)
CLIENT.loop_forever()
