from dataclasses import dataclass
from gpiozero import LED, Button
from mqtt_utils import publish
from typing import Optional
import paho.mqtt.client as mqtt_client

led_turn_off_topic = "iot/atividade/turnoff"

@dataclass
class State:
    leds: list[LED]
    buttons: list[Button]
    button_pressed_times: Optional[list[int]] = None

    def __post_init__(self):
        self.button_pressed_times = [0] * len(self.leds)

    def press_button1(self, client: Optional[mqtt_client.Client] = None, publish_: bool = False, topic: str = "iot"):
        """
        Button 1 is the first button of the self.buttons list.

        - If the first button is pressed for the first time, turn on the first led.
        - If the first button is pressed for the second time, turn on the second led.
        """
        idx = 0
        if self.button_pressed_times[idx] == 0:
            self.leds[idx].on()
            self.button_pressed_times[idx] += 1
        else:
            self.leds[idx+1].on()
            self.button_pressed_times[idx] = 0

        if publish_:
            publish(client, topic, "Button 1 pressed")

    def press_button2(self, client: Optional[mqtt_client.Client] = None, publish_: bool = False, topic: str = "iot"):
        """
        Button 2 is the second button of the self.buttons list.

        - If the second button is pressed, turn off all leds.
        """
        for i, led in enumerate(self.leds):
            led.off()
            self.button_pressed_times[i] = 0

        if publish_:
            publish(client, topic, "Button 2 pressed")

    def publish_state(self, client: Optional[mqtt_client.Client] = None, topic: str = "iot"):
        
        publish(client, topic, f"Leds states: {[led.is_active for led in self.leds]}")
        
        print(f"State published: {self}")

    def handle_message(self, topic: str, payload: str):
        print(f"{topic} : {payload}")
        if topic == led_turn_off_topic:
            for led in self.leds:
                led.off()

    def subscribe_to_topic(self, client, topic="iot/#"):
        client.subscribe(topic)
