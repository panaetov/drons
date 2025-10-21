import time

import paho.mqtt.client as mqtt
from geopy.distance import geodesic


BEACON_ID = 'beacon-1'
USERNAME = 'drons'
PASSWORD = 'drons'
CLIENT = mqtt.Client(
    protocol=mqtt.MQTTv5,
    client_id="my_publisher",
)
CLIENT.username_pw_set(USERNAME, PASSWORD)

CLIENT.connect('127.0.0.1', 1883)

receivers = [
    [55.751244, 37.618423],  # R0
    [55.759000, 37.618423],  # R1 — ~860 м севернее
    [55.751244, 37.630000],  # R2 — ~800 м восточнее
]

# Истинная позиция маячка
true_latlon = [55.755, 37.625]

now_ns = int(time.time() * 10**9)

# Симуляция времён (в реальности — измеряются)
c = 299_792_458.0
distances = []


for n in range(1):
    for dron_id, (lat, lon) in enumerate(receivers):


        d = geodesic((lat, lon), true_latlon).meters
        dt_ns = int(10**9 * d / c)

        toa_ns = now_ns + dt_ns
        CLIENT.publish(
            "beacon/detect",
            f"dron-{dron_id}:{lat}:{lon}:{BEACON_ID}:{now_ns}:{toa_ns}",
            qos=1,
        )
        print(f"Published {dron_id}")


import time
time.sleep(1)
CLIENT.disconnect()
