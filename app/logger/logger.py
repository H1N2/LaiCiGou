import time
from datetime import datetime

def info(msg):
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print('>> {0}: {1}'.format(t, msg))


if __name__ == '__main__':
    info('log A')
    time.sleep(2)
    info('log B')
