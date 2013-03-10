import flask
import gevent
from gevent import monkey; monkey.patch_all()

# Duration of the trigger pull in seconds
TRIGGER_TIME = 0.28
# The PWM channel to use for pulling the trigger
TRIGGER_PIN = 7 # 7= P1 pin 22

# PWM Frequency. Warning -- DO NOT CHANGE here without changing the PWM cycle time in pi-blaster.c
PWM_FREQ = 50
# PWM Period (seconds)
PWM_PERIOD = 1.0 / PWM_FREQ
# Counter-clockwise oscillation pulse width (seconds)
PWM_WIDTH_LEFT = 0.00125
OSC_LEFT_WIDTH = (PWM_PERIOD - PWM_WIDTH_LEFT) / PWM_PERIOD
# Clockwise oscillation pulse width
PWM_WIDTH_RIGHT = 0.00169
OSC_RIGHT_WIDTH = (PWM_PERIOD - PWM_WIDTH_RIGHT) / PWM_PERIOD
# Oscillation time (1/2 cycle, in seconds). Increase this to give the gun a wider area of fire.
OSC_PERIOD = 1.0
# Oscillation paruse time, in seconds
OSC_PAUSE = 0.5
# Oscillation channel
OSC_CHANNEL = 0 # 0= P1 pin 7

osc_thread = None
osc_end = False

# Up servo pulse width
TILT_UP_WIDTH = 0.1
# Down servo pulse width
TILT_DOWN_WIDTH = 0.2
# Time in seconds to spend tilting when a request comes in
TILT_TIME = 1
# Tilt channel
TILT_CHANNEL = 1 # 1= P1 pin 11

nerfer = flask.Flask(__name__)

@nerfer.route('/', methods=['GET', 'POST'])
def show_controls():
    if flask.request.method == 'GET':
        return flask.render_template('control.html')

    commands = []
    commands.append('Commands\n')
    commands.append('/fire: Fire a dart\n')
    commands.append('/osc-start: Start oscillating\n')
    commands.append('/osc-stop: Stop oscillating\n')
    commands.append('/tilt-up: Tilt up\n')
    commands.append('/tilt-down: Tilt down\n')
    return ''.join(commands)

@nerfer.route('/fire', methods=['GET', 'POST'])
def fire_dart():
    fire_thread = gevent.spawn(open_fire)
    if flask.request.method == 'GET':
        return flask.redirect('/')
    return 'pew!\n'

def open_fire():
    pwm_file = open('/dev/pi-blaster', 'w', 1)
    pwm_file.write('%s=1\n' % TRIGGER_PIN) 
    gevent.sleep(TRIGGER_TIME)
    pwm_file.write('%s=0\n' % TRIGGER_PIN)

@nerfer.route('/osc-start', methods=['GET', 'POST'])
def begin_oscillation():
    global osc_thread
    global osc_end

    stop_oscillation()

    if osc_thread is None:
        osc_thread = gevent.spawn(osc_loop)    

    if flask.request.method == 'GET':
        return flask.redirect('/')
    return 'oscillating\n'

@nerfer.route('/osc-stop', methods=['GET', 'POST'])
def stop_oscillation():
    global osc_thread
    global osc_end

    if osc_thread is None:
        if flask.request.method == 'GET':
            return flask.redirect('/')
        return 'done oscillating\n'

    if not osc_thread.ready():
        osc_end = True

    osc_thread = None
    if flask.request.method == 'GET':
        return flask.redirect('/')
    return 'done oscillating\n'

def osc_loop():
    global osc_end
    pwm_file = open('/dev/pi-blaster', 'w', 1)
    while not osc_end:
        pwm_file.write('%s=%s\n' % (OSC_CHANNEL, OSC_LEFT_WIDTH))
        gevent.sleep(OSC_PERIOD)
        pwm_file.write('%s=0\n' % OSC_CHANNEL)
        gevent.sleep(OSC_PAUSE)
        pwm_file.write('%s=%s\n' % (OSC_CHANNEL, OSC_RIGHT_WIDTH))
        gevent.sleep(OSC_PERIOD)
        pwm_file.write('%s=0\n' % OSC_CHANNEL)
        gevent.sleep(OSC_PAUSE) 

    pwm_file.write('%s=0\n' % OSC_CHANNEL)
    osc_end = False

@nerfer.route('/tilt-up', methods=['GET', 'POST'])
def begin_tilt_up():
    tilt_thread = gevent.spawn(do_tilt, TILT_UP_WIDTH)
    if flask.request.method == 'GET':
        return flask.redirect('/')
    return 'tilt up\n'

@nerfer.route('/tilt-down', methods=['GET', 'POST'])
def begin_tilt_down():
    tilt_thread = gevent.spawn(do_tilt, TILT_DOWN_WIDTH)
    if flask.request.method == 'GET':
        return flask.redirect('/')
    return 'tilt down\n'

def do_tilt(pulse_width):
    pwm_file = open('/dev/pi-blaster', 'w', 1)
    pwm_file.write('%s=%s\n' % (TILT_CHANNEL, pulse_width)) 
    gevent.sleep(TILT_TIME)
    pwm_file.write('%s=0\n' % TILT_CHANNEL)

if __name__ == '__main__':
    nerfer.debug = True
    nerfer.run(host='0.0.0.0')
