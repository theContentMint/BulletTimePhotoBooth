
import time
import arduinologger
import GoProRemote

ard = arduinologger.logger( serial_port='/dev/ttyACM0', filename='trigger_times.csv' )
ard.start()
g = gopro.gopro(filename='record_times.csv')
g.start()

running = True
while running:
    #result = raw_input('Press s to stop')
    #if result == 's':
    #    running = False
    try:
        time.sleep(0.5)
    except KeyboardInterrupt:
        break

g.stop()
ard.stop()
