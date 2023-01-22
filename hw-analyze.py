from tinydb import TinyDB, Query
from hwcapture.logging import get_logger
from hwcapture.packet import Packet, Monitor, BadPacket

logger = get_logger('DEBUG')

only_calls = ['subscriptionGetInfo']
only_calls = ['adventure_getPassed']
only_calls = None

def main():
    db = TinyDB('hw-capture.json')
    monitor = Monitor(only_calls=only_calls)

    for i, raw in enumerate(db.all()):
        try:
            monitor.process(Packet(raw, i))
        except BadPacket:
            pass

    monitor.report_debug()


if __name__ == '__main__':
    main()
