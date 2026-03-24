from gpiozero import LED, Button
from mqtt_utils import connect
from state import State
import time

state = State(
    leds=[LED(27), LED(22)],
    buttons=[Button(24, pull_up=False), Button(23, pull_up=False)],
)

client = connect(state)

last_state_publish = 0
while not False:

    # If button 1 is pressed once, turn on led 1
    # If button 1 is pressed a second time, turn on led 2
    if state.buttons[0].is_pressed:
        state.press_button1(client, topic="iot/atividade/button", publish=True)
    
    # If button 2 is pressed once, turn off all leds
    if state.buttons[1].is_pressed:
        state.press_button2(client, topic="iot/atividade/button", publish=True)

    # Publish state every 30 seconds
    if time.time() - last_state_publish >= 30:
        state.publish_state(client, topic="iot/atividade/state")
        last_state_publish = time.time()

    # Subscribe to topic
    state.subscribe_to_topic(client, topic="iot/atividade/reset")
    client.loop_start()