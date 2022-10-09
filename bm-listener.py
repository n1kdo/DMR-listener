#!/bin/python3

import datetime
import json
import logging
import socketio
import sys
import time


URL = 'https://api.brandmeister.network'
SIO_PATH = '/lh/socket.io'
INTERESTING_TALKGROUPS = [3113, 31130, 31131, 31132, 31133, 31134, 31135, 31136, 31137, 31138, 31139, 311340, 3113090, ]
LOGGED_CALLS_FILENAME = 'bm_logged_calls.txt'

write_files = True
last_ten = []  # this is used to help prevent duplicate records.

# all traffic from the interesting peers will be logged.
INTERESTING_PEERS = [
    310293,  # w4boc  stone mountain
    313132,  # w4boc  stone mountain
    310371,  # w4doc  atlanta
    #  310466,  # k4vyx  savannah
    #  310592,  # KG4BKO vidalia
    310969,  # W4KST  Marietta
    310996,  # KM4EYX Douglas GA (NEW)
    311303,  # KE4OKD Sandy Springs
    311313,  # w8red  snellville
    311314,  # KD4KHO Canton
    #311318,  # K4QHR  Kingsland
    311320,  # w4cba  cumming
    311321,  # n4taw  between
    311322,  # ka3jij gainesville
    #311337,  # wa4asi covington
    311338,  # kd4z   sweat mountain
    #311350,  # km4dnd waycross
    #311617,  # ke4pmp Parrot GA
    311637,  # NG4RF  Cumming
    312243,  # WA4OKJ Rome
    #312284,  # KD4IEZ Dublin
    #312288,  # AF1G   Kathleen
    #312384,  # KZ4FOX Athens
    #312391,  # KE4PMP Cochran
    #312429,  # KE4RJI Tifton
    #312444,  # KZ4FOX Athens
    #312477,  # WX4EMA Macon
    #312779,  # WY4EMA Kathleen
]

tg_remap = {
    'Tac 310 NOT A CALL CHANNEL': 'TAC310',
    'TAC 311 USA NO NETS!!!': 'TAC311',
    'TAC 312 USA NO NETS!!!': 'TAC312',
    'TAC 313 USA NO NETS!!!': 'TAC313',
    'TAC 314 USA NO NETS!!!': 'TAC314',
    'TAC 315 USA NO NETS!!!': 'TAC315',
    'TAC 316 USA NO NETS!!!': 'TAC316',
    'TAC 317 USA NO NETS!!!': 'TAC317',
    'TAC 318 USA NO NETS!!!': 'TAC318',
    'TAC 319 USA NO NETS!!!': 'TAC319',
}

def append_logged_calls(filename, new_calls):
    if write_files and new_calls is not None and len(new_calls) > 0:
        with open(filename, 'a') as datafile:
            for stuff in new_calls:
                line = '{},{},{},{},{},{},{},{},{},{},{}'.format(stuff['timestamp'],
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
    global last_ten
    global write_files
    calls_to_log = []
    raw_data = json.loads(data['payload'])
    try:
        if raw_data.get('Event', '').strip() == 'Session-Stop':
            destination_id = safe_int(raw_data.get('DestinationID', '-1'))
            context_id = safe_int(raw_data.get('ContextID', '-1'))
            if destination_id in INTERESTING_TALKGROUPS or context_id in INTERESTING_PEERS:
                #  print('len(last_ten)={}'.format(len(last_ten)))
                if raw_data in last_ten:
                    print('duplicate!', raw_data)
                else:
                    last_ten.insert(0, raw_data)
                    if len(last_ten) > 10:
                        last_ten = last_ten[:10]
                    start = safe_int(raw_data.get('Start', '0'))
                    end = safe_int(raw_data.get('Stop', '0'))
                    elapsed = end - start
                    destination_name = raw_data.get('DestinationName', '').strip()
                    destination_name = destination_name.replace(' - 10 Minute Limit', '')
                    destination_name = tg_remap.get(destination_name, destination_name)
                    destination_id = raw_data.get('DestinationID', -1)
                    if len(destination_name) == 0 or destination_name == 'Cluster':
                        destination_name = str(destination_id)
                    source_id = raw_data.get('SourceID', 0)
                    source_call = raw_data.get('SourceCall', '').strip()
                    source_name = raw_data.get('SourceName', '').strip()
                    link_call = raw_data.get('LinkCall', '').strip()
                    if link_call == '':
                        if context_id == source_id:
                            link_call = '({})'.format(source_call)

                    link_name = raw_data.get('LinkName', '').strip()
                    total_count = safe_int(raw_data.get('TotalCount', '0'))

                    if elapsed < 1 and total_count < 5:
                        print('Kerchunk! start: {} end:{} elapsed: {} total_count: {} destination: {} sourcecall: {}'.format(start, end, elapsed, total_count, destination_name, source_call))

                    call = {
                        'timestamp': convert_brandmeister_timestamp(end),
                        'site': link_name,
                        'dest': destination_name,
                        'peer_id': context_id,
                        'peer_callsign': link_call,
                        'peer_name': link_name,
                        'radio_id': source_id,
                        'radio_callsign': source_call,
                        'radio_username': source_name,
                        'duration': elapsed,
                        'sourcepeer': '{} -- {}'.format(link_call, context_id)
                    }

                    line = '{},{},{},{},{},{},{},{},{},{},{}'.format(convert_brandmeister_timestamp(end),
                                                                     link_name,
                                                                     destination_name,
                                                                     context_id,
                                                                     link_call,
                                                                     link_name,
                                                                     source_id,
                                                                     source_call,
                                                                     source_name,
                                                                     elapsed,
                                                                     '{} -- {}'.format(link_call, context_id),
                                                                     )

                    calls_to_log.append(call)
                    if not write_files:
                        print(raw_data)
                        print(line)
                        print()
    except KeyError as ke:
        print(ke)
        print(raw_data)

    if len(calls_to_log) > 0:
        append_logged_calls(LOGGED_CALLS_FILENAME, calls_to_log)
        calls_to_log = []


@sio.event
def disconnect():
    print('disconnected')


def main():
    global write_files
    global last_ten
    print('starting')
    write_files = True
    last_ten = []
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == 'test':
            write_files = False
            print('NOT writing files -- debug mode.')
            logging.basicConfig(level=logging.DEBUG)
            logging.root.level = logging.DEBUG
    sio.connect(url=URL, socketio_path=SIO_PATH, transports='websocket')
    sio.wait()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:{}',
                        level=logging.INFO)
    logging.Formatter.converter = time.gmtime
    main()

