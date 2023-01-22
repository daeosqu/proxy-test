import re
import json
from collections import UserDict, UserList
from hwcapture.logging import get_logger


MYSERVER = 145
DEFAULT_IGNORE_CALLS = ('registration', 'bundleGetAllAvailableId', 'invasion_getInfo', 'stronghold_getInfo', 'getTime')
logger = get_logger('DEBUG')

AUTO_IGNORE_PATTERNS = {}


class NULL:
    pass


class BadPacket(ValueError):
    pass


def omit_string(text, maxlen=None):
    if maxlen is None:
        maxlen = 512
    if maxlen < 0:
        return text
    length = len(text)
    if length > maxlen:
        text = text[:maxlen]
        text = text.rstrip('\t \n')
        if type(text) is str:
            text += f'\n//... (length: {length})'
        else:
            text += f'\n//...(bytes: {length})'.encode('utf-8')
            text = text.decode('utf-8', 'surrogatepass')
    return text


class Packet:
    """パケット"""
    def __init__(self, packet, packet_id=None):
        self.packet_id = packet_id
        self.packet = packet

    def get_event_generator(self):
        return EventGenerator(self)

    @property
    def names(self):
        return [call['name'] for call in self.packet['request']['calls']]

    @property
    def idname(self):
        if self.packet_id is None:
            return '#?'
        else:
            return '#' + str(self.packet_id)

    def __getitem__(self, name):
        return self.packet[name]

    def __str__(self):
        # eg. "#10 ['arenaFindEnemies']"
        return f'{self.idname} {self.names}'


# KNOWN_COMMANDS = ('body', 'getTime', 'userGetInfo', 'friendsGetInfo', 'billingGetAll', 'inventoryGet')
# DEBUG_UNKNOWN_COMMANDS = []


class Event:
    """パケット内の calls および result を１対にまとめたデータ"""
    def __init__(self, packet, event_index):
        self.packet = packet
        self.index = event_index
        self.call = packet['request']['calls'][event_index]
        self.name = self.call['name']
        # 通常 response.results[event_index].result.response が call に対応する
        # レスポンスの値になります。
        result_value = packet['response']['results'][event_index]
        ident = result_value['ident']
        # if not re.match('(body|group_[0-9]+_body|getTime|userGetInfo|friendsGetInfo|billingGetAll|inventoryGet)$', ident):
        #     logger.warning(f'Unknown ident: ident="{ident}", call={packet}.{event_index}')
        #     DEBUG_UNKNOWN_COMMANDS.append(ident)
        #self.result = result_value
        self.result = result_value["result"]["response"]

    def __str__(self):
        # eg. "#10.0.arenaFindEnemies"
        return f'{self.packet.idname}.{self.index}.{self.name}'

    def dump(self, omit=NULL, omit_result=NULL, no_header=False):
        if omit is NULL and omit_result is NULL:
            omit = 512
            omit_result = None
        else:
            if omit is NULL:
                omit = 512
            if omit_result is NULL:
                omit_result = omit
        req_dump = omit_string(json.dumps(self.call), omit)
        res_dump = omit_string(json.dumps(self.result, indent=2), omit_result)
        if no_header:
            return req_dump + '\n' + res_dump
        else:
            return f'{str(self)}: ' + req_dump + '\n' + res_dump


class EventGenerator:
    """イベントのジェネレーター"""
    def __init__(self, packet):
        self.packet = packet
        self.calls = packet['request']['calls']
        try: # DEBUG
            self.results = packet['response']['results']
        except KeyError:
            __import__("ipdb").set_trace()

        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index == len(self.calls):
            raise StopIteration()
        event = Event(self.packet, self.index)
        self.index += 1
        return event


class User(UserDict):
    def __init__(self, user):
        super().__init__(user)

    def summary(self, verbosity=0):
        name = f'{self["name"]}({self["level"]})'
        return name

    def __str__(self):
        return self.summary()

    def __repr__(self):
        return self.summary()


class Hero(UserDict):
    def __init__(self, user):
        super().__init__(user)

    def summary(self, verbosity=0):
        return f'{self["id"]} {self["level"]}.{self["color"]}.{self["star"]}'

    def __str__(self):
        return self.summary()

    def __repr__(self):
        return self.summary()


class HeroSet(UserList):
    def __init__(self, heroes):
        heroes = [Hero(h) for h in heroes]
        super().__init__(heroes)

    def summary(self, verbosity=0):
        return '[' + ', '.join(map(str, self)) + ']'

    def __str__(self):
        return self.summary()

    def __repr__(self):
        return self.summary()


class ArenaEnemy(UserDict):
    def __init__(self, data):
        keys = ('place', 'power')
        newdict = {k: data[k] for k in data if k in keys}
        newdict['user'] = User(data['user'])
        newdict['heroes'] = HeroSet(data['heroes'])
        super().__init__(newdict)

    def summary(self, verbosity=0):
        return f'{self["place"]} {self["user"]} {self["power"]} {self["heroes"]}'

    def __str__(self):
        return self.summary()

    def __repr__(self):
        return self.summary()


class EventHandler:
    def __init__(self):
        self.need_blank = False

    def arenaFindEnemies(self, event):
        print()
        for i, user in enumerate(event.result):
            print(f'ARENA#{i}', ArenaEnemy(user))

    def userGetInfo(self, event):
        result = event.result
        print(f'exp: {result["experience"]}')

    def adventure_getPassed(self, event):
        result = event.result
        print(json.dumps(result))

    def subscriptionGetInfo(self, event):
        reward_summary = []

        result = event.result
        s = result["subscription"]
        r = result["dailyReward"]

        level = s["level"]
        reward_summary.append(f"LV:{level}")

        coin = {}
        for k,v in r["currentReward"]["coin"].items():
            if k == "14":
                k = "coin"
            coin[k] = v
        if len(coin.keys()) > 0:
            reward_summary.append(str(coin))
        else:
            reward_summary.append("No reward")
        not_farmed_days = r["notFarmedDays"]
        if not_farmed_days:
            reward_summary.append("(Not farmed days: {not_farmed_days})")

        days_left = s["daysLeft"]
        reward_summary.append(f"{days_left} days left")

        print(' '.join(reward_summary))


    def stashClient(self, event):
        data = event.call["args"]["data"]
        for item in data:
            if item["type"] == ".client.window.open":
                window = item["params"]["windowName"]
                print(f'Open window "{window}"')
                return
        raise BadPacket("No client.window.open data in stashCleient call")

    def _default(self, event, omit=NULL, omit_result=NULL):
        dump = event.dump(no_header=True)
        print(str(event) + " (Not implemented)" + dump)
        AUTO_IGNORE_PATTERNS[event.call["name"]] = event.result

    def __call__(self, event):
        if event.name.startswith('_'):
            raise ValueError('Bad event name')
        function = getattr(self, event.name, None)
        if function:
            print()
            print(str(event) + ": ", end="")
            function(event)
            self.need_blank = True
            return True
        else:
            if self.need_blank:
                self.need_blank = False
                print()
            self._default(event)
            return False


class Monitor:
    def __init__(self, *, handler=None, filter=None, ignore_calls=None, only_calls=None, ignore_file=".hwpacket-ignore"):
        self.handler = handler if handler else EventHandler()
        self.only_calls = only_calls
        self.ignore_calls = ignore_calls if ignore_calls else DEFAULT_IGNORE_CALLS
        self.filter = filter
        if ignore_file:
            self.ignores = self.load_ignore(ignore_file)

    def load_ignore(self, filename):
        try:
            with open(filename, "r") as fh:
                data = json.loads(fh.read())
                for k,v in data.items():
                    if v is not None:
                        data[k] = json.dumps(v)
                logger.info(f'{filename} loaded.')
        except FileNotFoundError:
            return []

    def process(self, packet, ignore_calls=None):
        all_accepted = True

        for event in packet.get_event_generator():
            accept = None

            if self.filter:
                accept = self.filter(event)
                reason = "filter"

            if accept is None:
                if self.only_calls:
                    accept = event.name in self.only_calls
                    reason = "only_calls"
                else:
                    accept = event.name not in self.ignore_calls
                    if not accept:
                        reason = "ignore_calls"
                    if accept and self.ignores:
                        if event.name in self.ignores:
                            value = self.ignores[event.name]
                            if value is None:
                                accept = False
                                reason = ".hwpacket-ignore"
                            elif value == json.dumps(event.result):
                                accept = False
                                reason = ".hwpacket-ignore"

            if not accept:
                logger.debug(f'SKIP {event} (filtered by "{reason}")')
                all_accepted = False
                continue

            try:
                if not self.handler(event):
                    all_accepted = False
            except Exception as exc:
                print(event)
                raise

        return all_accepted

    def report_debug(self):
        num = len(AUTO_IGNORE_PATTERNS.keys())
        if num > 0:
            with open(".hwpacket-ignore.auto", "w") as fh:
                fh.write(json.dumps(AUTO_IGNORE_PATTERNS, indent=2))
            logger.info(f"wrote .hwpacket-ignore.auto ({num} entries)")
