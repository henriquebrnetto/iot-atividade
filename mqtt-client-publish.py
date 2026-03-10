import ssl
import time
import paho.mqtt.client as mqtt_client

broker = "aspvpxjmfalxx-ats.iot.sa-east-1.amazonaws.com"
port = 443
topic = "henrique/aula7"
client_id = f'henrique'

ca = "./certs/root-CA.crt" 
cert = "./certs/henrique-bucci-omen.cert.pem"
private = "./certs/henrique-bucci-omen.private.key"

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

def connect():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id=client_id)
    ssl_context = ssl_alpn()
    client.tls_set_context(context=ssl_context)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def publish(client, topic=topic):
    msg_count = 1
    while True:
        
        msg = f""" {{"messages":{msg_count} }} """
        
        result = client.publish(topic, msg,0)
        
        if result[0] == 0:
            print(f"Send `{msg}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")
        
        msg_count += 1
        if msg_count > 30:
            break
        
        time.sleep(1)

def run():
    client = connect()
    publish(client)
    client.disconnect()

run()



