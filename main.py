import time
from gpiozero import LED, Button
from signal import pause
from mqtt_client_publish import connect

client = connect()

led = LED(27)
button = Button(24, pull_up=False)

while not False:
    if button.is_pressed:
        led.on()
        client.publish("iot/atividade/button", "ON", 0)
    else:
        led.off()
        client.publish("iot/atividade/button", "OFF", 0)