from gpiozero import LED, Button
import time
from signal import pause

led = LED(27)
button = Button(24, pull_up=False)

led.source = button

pause()