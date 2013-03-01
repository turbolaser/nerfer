import flask
import gevent
from gevent import monkey; monkey.patch_all()

# Duration of the trigger pull in seconds
TRIGGER_TIME = 0.5
# The PWM channel to use for pulling the trigger
TRIGGER_PIN = 7 # 7= P1 pin 22

# Left oscillation pulse width (in hundredths of seconds - 0.1 for 1 ms)
OSC_LEFT_WIDTH = 0.1
# Right oscillation pulse width
OSC_RIGHT_WIDTH = 0.2
# Oscillation time (1 complete cycle, in seconds)
OSC_PERIOD = 0.2
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

@nerfer.route('/')
def hello_world():
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

    return 'oscillating\n'

@nerfer.route('/osc-stop', methods=['GET', 'POST'])
def stop_oscillation():
    global osc_thread
    global osc_end

    if osc_thread is None:
        return 'done oscillating\n'

    if not osc_thread.ready():
        osc_end = True

    osc_thread = None
    return 'done oscillating\n'

def osc_loop():
    global osc_end
    pwm_file = open('/dev/pi-blaster', 'w', 1)
    while not osc_end:
        pwm_file.write('%s=%s\n' % (OSC_CHANNEL, OSC_LEFT_WIDTH))
        gevent.sleep(OSC_PERIOD / 2.0)
        pwm_file.write('%s=%s\n' % (OSC_CHANNEL, OSC_RIGHT_WIDTH))
        gevent.sleep(OSC_PERIOD / 2.0) 

    pwm_file.write('%s=0\n' % OSC_CHANNEL)
    osc_end = False

@nerfer.route('/tilt-up', methods=['GET', 'POST'])
def begin_tilt_up():
    tilt_thread = gevent.spawn(do_tilt, TILT_UP_WIDTH)
    return 'tilt up\n'

@nerfer.route('/tilt-down', methods=['GET', 'POST'])
def begin_tilt_down():
    tilt_thread = gevent.spawn(do_tilt, TILT_DOWN_WIDTH)
    return 'tilt down\n'

def do_tilt(pulse_width):
    pwm_file = open('/dev/pi-blaster', 'w', 1)
    pwm_file.write('%s=%s\n' % (TILT_CHANNEL, pulse_width)) 
    gevent.sleep(TILT_TIME)
    pwm_file.write('%s=0\n' % TILT_CHANNEL)

if __name__ == '__main__':
    # nerfer.debug = True
    nerfer.run(host='0.0.0.0')
