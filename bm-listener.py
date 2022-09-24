#!/bin/python3

import datetime
import json
import socketio


URL = 'https://api.brandmeister.network'
SIO_PATH = '/lh/socket.io'
INTERESTING_TALKGROUPS = [3113, 31130, 31131, 31132, 31133, 31134, 31135, 31136, 31137, 31138, 31139, 311340, 3113090, ]
LOGGED_CALLS_FILENAME = 'bm_logged_calls.txt'

# all traffic from the interesting peers will be logged.  Best to not turn on brandmeister.
INTERESTING_PEERS = [
    310293,  # w4boc  stone mountain
    310371,  # w4doc  atlanta
    310466,  # k4vyx  savannah
    310592,  # KG4BKO vidalia
    310969,  # W4KST  Marietta
    310996,  # KM4EYX Douglas GA (NEW)
    311303,  # KE4OKD Sandy Springs
    311313,  # w8red  snellville
    311314,  # KD4KHO Canton
    311318,  # K4QHR  Kingsland
    311320,  # w4cba  cumming
    311321,  # n4taw  between
    311322,  # ka3jij gainesville
    311337,  # wa4asi covington
    311338,  # kd4z   sweat mountain
    311350,  # km4dnd waycross
    311617,  # ke4pmp Parrot GA
    311637,  # NG4RF  Cumming
    312243,  # WA4OKJ Rome
    312284,  # KD4IEZ Dublin
    312288,  # AF1G   Kathleen
    312384,  # KZ4FOX Athens
    312391,  # KE4PMP Cochran
    312429,  # KE4RJI Tifton
    312444,  # KZ4FOX Athens
    312477,  # WX4EMA Macon
]

DESTINATION_REMAP = {
    'Georgia - 10 Minute Limit': 'GAState Brandmeister',
}


def append_logged_calls(filename, new_calls):
    if new_calls is not None and len(new_calls) > 0:
        with open(filename, 'a') as datafile:
            for stuff in new_calls:
                line = '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s' % (stuff['timestamp'],
                                                             stuff['site'],
                                                             stuff['dest'],
                                                             stuff['peer_id'],
                                                             stuff['peer_callsign'],
                                                             stuff['peer_name'],
                                                             stuff['radio_id'],
                                                             stuff['radio_callsign'],
                                                             stuff['radio_username'],
                                                             stuff['duration'],
                                                             stuff['sourcepeer'],
                                                             )
                datafile.write(line + '\n')


def safe_int(s, default=-1):
    try:
        return int(s)
    except ValueError:
        return default


def convert_brandmeister_timestamp(s):
    try:
        dt = datetime.datetime.fromtimestamp(s)
        return dt.isoformat()
    except ValueError as e:
        print(e)
        return None


sio = socketio.Client()


@sio.event
def connect():
    print('connected')


@sio.on('mqtt')
def mqtt(data):
    calls_to_log = []
    raw_data = json.loads(data['payload'])
    try:
        if raw_data['Event'] == 'Session-Stop':
            destination_id = safe_int(raw_data['DestinationID'])
            context_id = safe_int(raw_data['ContextID'])
            if destination_id in INTERESTING_TALKGROUPS or context_id in INTERESTING_PEERS:
                start = safe_int(raw_data['Start'])
                end = safe_int(raw_data['Stop'])
                elapsed = end - start
                destination_name = raw_data['DestinationName']
                if destination_name in DESTINATION_REMAP:
                    destination_name = DESTINATION_REMAP[destination_name]
                destination_id = raw_data['DestinationID']
                if len(destination_name.strip()) == 0:
                    destination_name = str(destination_id)
                source_id = raw_data['SourceID']
                source_call = raw_data['SourceCall']
                source_name = raw_data['SourceName']
                link_call = raw_data['LinkCall']
                link_name = raw_data['LinkName']

                call = {
                    'timestamp': convert_brandmeister_timestamp(end),
                    'site': link_name,
                    'dest': destination_name,
                    'peer_id': context_id,
                    'peer_callsign': link_call,
                    'peer_name': source_name,
                    'radio_id': source_id,
                    'radio_callsign': source_call,
                    'radio_username': source_name,
                    'duration': elapsed,
                    'sourcepeer': '{} -- {}'.format(link_call, context_id)
                }
                calls_to_log.append(call)
                print(raw_data)
                #print(call)
                #print()
    except KeyError as ke:
        print(ke)
        print(raw_data)

    if len(calls_to_log) > 0:
        append_logged_calls(LOGGED_CALLS_FILENAME, calls_to_log)


@sio.event
def disconnect():
    print('disconnected')


def main():
    print('starting')
    sio.connect(url=URL, socketio_path=SIO_PATH, transports='websocket')
    sio.wait()


if __name__ == '__main__':
    main()

