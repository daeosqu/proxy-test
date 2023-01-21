#!/usr/bin/python3

# Usage:
# mitmdump --quiet --flow-detail 0 -s ./anatomy.py

# NOTE
# '/home/daisuke/.cache/pypoetry/virtualenvs/proxy-test-Yuu0BkCc-py3.10/lib/python3.10/site-packages/mitmproxy/http.py'

import logging
import json
import re
from mitmproxy.http import Request, Response, Message
from tinydb import TinyDB, Query

from hw_packet import Packet, Monitor


def omit_string(text, maxlen=512):
    length = len(text)
    if length > maxlen:
        text = text[:maxlen]
        text = text.rstrip('\t \n')
        if type(text) is str:
            text += f'\n... (length: {length})'
        else:
            text += f'\n...(bytes: {length})'.encode('utf-8')
            text = text.decode('utf-8', 'surrogatepass')
    return text


def to_json_log(message: Message):
    if isinstance(message, Request):
        name = '#request'
    elif isinstance(message, Response):
        name = '#response'
    else:
        raise ValueError('Illegal argument')
    try:
        return json.dumps(message.json(), indent=2)
    except json.decode.JSONDecodeError:
        return json.dumps({name: message.text})


def is_not_important_websocket_message(data):
    method = data.get('method')
    if method == 'msg':
        type_ = data.get('type')
        if type_ == 'newMail':
            return False

    cells = data.get('cells')
    if type(cells) is list:
        for c in cells:
            name = c.get('name')
            if name == 'stashClient':
                args = c.get('args')
                if args:
                    data = args.get('data')
                    if type(data) is list:
                        for l in list:
                            type_ = l.get('type')
                            if type_ == '.client.window.open':
                                print('ignore .client.window.open')
                                return False
    return True


class HWCapture:
    def __init__(self):
        self.num = 0
        self.db = TinyDB('hw-capture.json')
        self.monitor = Monitor()

    def convert_to_packet_data(self, flow):
        data = {
            'url': flow.request.url,
            'request': flow.request.json(),
            'response': flow.response.json(),
        }
        return data

    def websocket_message(self, flow):
        """
            Called when a WebSocket message is received from the client or
            server. The most recent message will be flow.messages[-1]. The
            message is user-modifiable. Currently there are two types of
            messages, corresponding to the BINARY and TEXT frame types.
        """
        return

        for flow_msg in flow.websocket.messages:
            if 'pushd.nextersglobal.com' not in flow.request.url:
                continue

            direction = '>>' if flow_msg.from_client else '<<'
            packet = flow_msg.content
            text = None
            data = None

            try:
                text = packet.decode()
                try:
                    data = json.loads(text)
                except json.decode.JSONDecodeError as exc:
                    print(f"JSON decode error: {exc}")
            except UnicodeDecodeError as exc:
                print("UTF-8 decode error: {exc}")
            else:
                if data is not None:
                    if data.get('method') == 'auth':
                        continue
                    if data.get('method') == 'ping':
                        if data in ({'method': 'ping'}, {'method': 'ping', 'result': 'pong', 'error': None}):
                            continue

                    text = json.dumps(data)
                    text = omit_string(text)
                    if direction == '<<':
                        if is_not_important_websocket_message(data):
                            pass #print('SKIP!', text)


            print(direction, text)


    def response(self, flow):

        req = flow.request

        if re.search('(/|\.)(google|googleapis|googlevideo|gstatic|akamaihd|youtube)\.(com|net)(/|$)', req.url):
            return

        if not re.search('(/|\.)(nextersglobal)\.(com)(/|$)', req.url):
            print(req.url)
            return

        if req.url == "https://pushd.nextersglobal.com/websocket":
            return
        if req.url == "https://error.nextersglobal.com/client/":
            return

        print()
        print(f"{req.method} {req.url}")

        if req.method != 'POST':
            print("Method is not POST!")

        content_type = req.headers.get('content-type')
        req_data = None
        if content_type is None:
            print("Content type is None!")
        else:
            pass
            # if content_type != 'application/json; charset=UTF-8':
            #     print(f"Unexpected content-type header in request: content-type={content_type}")
            #     req_data = req.text
            # else:
            #     try:
            #         req_data = req.json()
            #     except json.decoder.JSONDecodeError:
            #         req_data = req.text
            # req_data = omit_string(req_data)
            # print(f"Request: {req_data}")

        res = flow.response
        if res.status_code != 200:
            print(f"Status code is not 200: status_code={res.status_code}")

        content_type = res.headers.get('content-type')
        text = res.text

        if content_type != "application/javascript; charset=utf-8":
            print(f"Unexpected content-type header in response: content-type={content_type}")
        else:
            try:
                res_data = res.json()
            except json.decoder.JSONDecodeError as exc:
                print(f"JSON decode error: {exc}")
            else:
                text = json.dumps(res_data, indent=2)

                req_log = json.dumps

                with open("output.txt", mode="a") as fh:
                    fh.write('#' + req.url + '\n')
                    fh.write('[\n')
                    fh.write(to_json_log(req))
                    fh.write('\n,\n')
                    fh.write(to_json_log(res))
                    fh.write('\n]\n')
                    fh.write('\n')

                packet_data = self.convert_to_packet_data(flow)
                self.db.insert(packet_data)
                self.monitor.process(Packet(packet_data))

        # text = omit_string(text)
        # print(f"Response: {text}")


addons = [HWCapture()]
