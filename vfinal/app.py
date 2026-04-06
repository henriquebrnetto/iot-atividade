import json
import ssl
import time
import threading
from datetime import datetime

import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt

# =========================
# CONFIGURAÇÃO DOS GPIOs
# =========================
LED1_PIN = 17
LED2_PIN = 27
BUTTON1_PIN = 22
BUTTON2_PIN = 23

# =========================
# CONFIGURAÇÃO MQTT / AWS
# =========================
MQTT_BROKER = "aspvpxjmfalxx-ats.iot.sa-east-1.amazonaws.com"
MQTT_PORT = 8883

TOPIC_BUTTON = "insper/atividade1/botoes"
TOPIC_STATUS = "insper/atividade1/status"
TOPIC_RESET = "insper/atividade1/reset"

CLIENT_ID = "raspberrypi-atividade1"

# Caminhos dos certificados (AWS IoT Core)
CA_PATH = "/home/pi/certs/AmazonRootCA1.pem"
CERT_PATH = "/home/pi/certs/device.pem"
KEY_PATH = "/home/pi/certs/device.key"

# =========================
# ESTADO DOS LEDs
# =========================
led1_state = False
led2_state = False

# Conta quantas vezes o botão 1 foi pressionado
button1_press_count = 0

# Lock para evitar problemas entre threads
state_lock = threading.Lock()


# =========================
# FUNÇÕES GPIO
# =========================
def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(LED1_PIN, GPIO.OUT)
    GPIO.setup(LED2_PIN, GPIO.OUT)

    # Botões com pull-up interno
    GPIO.setup(BUTTON1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(BUTTON2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.output(LED1_PIN, GPIO.LOW)
    GPIO.output(LED2_PIN, GPIO.LOW)


def apply_led_states():
    GPIO.output(LED1_PIN, GPIO.HIGH if led1_state else GPIO.LOW)
    GPIO.output(LED2_PIN, GPIO.HIGH if led2_state else GPIO.LOW)


def turn_off_all_leds():
    global led1_state, led2_state, button1_press_count

    with state_lock:
        led1_state = False
        led2_state = False
        button1_press_count = 0
        apply_led_states()


def get_status_payload():
    with state_lock:
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "led1": "on" if led1_state else "off",
            "led2": "on" if led2_state else "off"
        }


# =========================
# FUNÇÕES MQTT
# =========================
def publish_button_event(client, button_name, action):
    payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "button": button_name,
        "action": action,
        "led_status": {
            "led1": "on" if led1_state else "off",
            "led2": "on" if led2_state else "off"
        }
    }

    client.publish(TOPIC_BUTTON, json.dumps(payload), qos=1)
    print(f"[MQTT] Evento publicado em {TOPIC_BUTTON}: {payload}")


def publish_status(client):
    payload = get_status_payload()
    client.publish(TOPIC_STATUS, json.dumps(payload), qos=1)
    print(f"[MQTT] Status publicado em {TOPIC_STATUS}: {payload}")


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("[MQTT] Conectado com sucesso ao broker")
        client.subscribe(TOPIC_RESET, qos=1)
        print(f"[MQTT] Inscrito no tópico: {TOPIC_RESET}")
    else:
        print(f"[MQTT] Falha na conexão. Código: {rc}")


def on_message(client, userdata, msg):
    print(f"[MQTT] Mensagem recebida no tópico {msg.topic}: {msg.payload.decode()}")

    if msg.topic == TOPIC_RESET:
        turn_off_all_leds()
        print("[AÇÃO] Mensagem recebida: todos os LEDs foram apagados")
        publish_status(client)


def create_mqtt_client():
    client = mqtt.Client(client_id=CLIENT_ID)

    client.on_connect = on_connect
    client.on_message = on_message

    # TLS para AWS IoT Core
    client.tls_set(
        ca_certs=CA_PATH,
        certfile=CERT_PATH,
        keyfile=KEY_PATH,
        cert_reqs=ssl.CERT_REQUIRED,
        tls_version=ssl.PROTOCOL_TLSv1_2
    )

    return client


# =========================
# CALLBACKS DOS BOTÕES
# =========================
def button1_callback(channel):
    global button1_press_count, led1_state, led2_state

    time.sleep(0.05)  # debounce simples
    if GPIO.input(BUTTON1_PIN) == GPIO.LOW:
        with state_lock:
            button1_press_count += 1

            if button1_press_count == 1:
                led1_state = True
            elif button1_press_count == 2:
                led2_state = True
            else:
                # Se quiser manter somente a lógica do slide:
                # após a segunda vez, continua como está
                pass

            apply_led_states()

        print("[GPIO] Botão 1 pressionado")
        publish_button_event(mqtt_client, "button1", "pressed")


def button2_callback(channel):
    time.sleep(0.05)  # debounce simples
    if GPIO.input(BUTTON2_PIN) == GPIO.LOW:
        turn_off_all_leds()
        print("[GPIO] Botão 2 pressionado - todos os LEDs desligados")
        publish_button_event(mqtt_client, "button2", "pressed")


# =========================
# THREAD DE STATUS A CADA 30s
# =========================
def status_publisher_loop():
    while True:
        publish_status(mqtt_client)
        time.sleep(30)


# =========================
# MAIN
# =========================
setup_gpio()

mqtt_client = create_mqtt_client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
mqtt_client.loop_start()

# Interrupções dos botões
GPIO.add_event_detect(BUTTON1_PIN, GPIO.FALLING, callback=button1_callback, bouncetime=300)
GPIO.add_event_detect(BUTTON2_PIN, GPIO.FALLING, callback=button2_callback, bouncetime=300)

# Thread para publicar status a cada 30 segundos
status_thread = threading.Thread(target=status_publisher_loop, daemon=True)
status_thread.start()

print("Sistema iniciado. Aguardando botões e mensagens MQTT...")

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nEncerrando aplicação...")

finally:
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    GPIO.cleanup()