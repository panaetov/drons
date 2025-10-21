import time

import paho.mqtt.client as mqtt
from geopy.distance import geodesic

IP = '127.0.0.1'
IP = '89.169.181.181'

BEACON_ID = 'beacon-1'

CLIENT = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="my_publisher",
)

CLIENT.connect(IP, 1883)

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

for dron_id, (lat, lon) in enumerate(receivers):
    print(f"Publishing dron {dron_id}")

    d = geodesic((lat, lon), true_latlon).meters
    dt_ns = int(10**9 * d / c)

    toa_ns = now_ns + dt_ns
    CLIENT.publish(
        "beacon/detect",
        f"dron-{dron_id}:{lat}:{lon}:{BEACON_ID}:{now_ns}:{toa_ns}"
    )

CLIENT.disconnect()
