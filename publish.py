import paho.mqtt.client as mqtt


CLIENT = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id="my_publisher",
)

CLIENT.connect("localhost", 1883)


CLIENT.publish("signal/catched", "")
CLIENT.disconnect()
