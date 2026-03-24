import ssl
import time
import paho.mqtt.client as mqtt_client
from dotenv import load_dotenv
import os

load_dotenv()

broker = os.getenv("BROKER")
port = os.getenv("PORT")
topic = os.getenv("TOPIC")
client_id = os.getenv("CLIENT_ID")

ca = os.getenv("CA")
cert = os.getenv("CERT")
private = os.getenv("PRIVATE")


def ssl_alpn():
    try:
        ssl_context = ssl.create_default_context()
        ssl_context.set_alpn_protocols(["x-amzn-mqtt-ca"])
        ssl_context.load_verify_locations(cafile=ca)
        ssl_context.load_cert_chain(certfile=cert, keyfile=private)

        return  ssl_context
    except Exception as e:
        print("exception ssl_alpn()")
        raise e


def connect(state=None):
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id=client_id)

    if state:
        client.user_data_set(state)

    ssl_context = ssl_alpn()
    client.tls_set_context(context=ssl_context)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(broker, port)
    return client


def publish(client, topic=topic, message=""):
    try:
        result = client.publish(topic, message, 0)
    except Exception as e:
        print("exception publish()")
        raise e
    
    if result[0] == 0:
        print(f"Send `{message}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")


def on_message(client, userdata, message):
    payload = message.payload.decode("utf-8")
    topic = message.topic

    state = userdata
    state.handle_message(topic, payload)