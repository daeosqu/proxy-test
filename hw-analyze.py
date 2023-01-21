from tinydb import TinyDB, Query
from hw_logging import get_logger
from hw_packet import Packet, Monitor

logger = get_logger('DEBUG')

only_calls = ['subscriptionGetInfo']
only_calls = ['adventure_getPassed']
only_calls = None

def main():
    db = TinyDB('hw-capture.json')
    monitor = Monitor(only_calls=only_calls)

    for i, raw in enumerate(db.all()):
        monitor.process(Packet(raw, i))

    monitor.report_debug()


if __name__ == '__main__':
    main()
