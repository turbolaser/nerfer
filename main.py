import flask
import RPi.GPIO as gpio
import time
import threading

# Duration of the trigger pull in seconds
TRIGGER_TIME = 5
# The GPIO to use for pulling the trigger
TRIGGER_PIN = 17

nerfer = flask.Flask(__name__)

@nerfer.route('/')
def hello_world():
    return 'Hello World!'

@nerfer.route('/fire')
def fire_dart():
    gpio.output(TRIGGER_PIN, gpio.HIGH)
    end_thread = threading.Thread(target=cancel_fire)
    end_thread.start()
    return 'pew!'

def cancel_fire():
    time.sleep(TRIGGER_TIME)
    gpio.output(TRIGGER_PIN, gpio.LOW)

if __name__ == '__main__':
    gpio.setmode(gpio.BOARD)
    gpio.setup(TRIGGER_PIN, gpio.OUT)
    nerfer.run()