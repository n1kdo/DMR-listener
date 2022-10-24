#!/bin/python3

import datetime
import json
import logging
import socketio
import sys
import time

from common import interesting_peer_ids
from common import talk_group_alias_to_number_dict
from common import talk_group_number_to_name_dict
from common import talk_group_network_number_to_name_dict

URL = 'https://api.brandmeister.network'
SIO_PATH = '/lh/socket.io'
INTERESTING_TALKGROUPS = [3113, 31130, 31131, 31132, 31133, 31134, 31135, 31136, 31137, 31138, 31139, 311340, 3113090, ]
LOGGED_CALLS_FILENAME = 'bm_logged_calls.txt'
DUPLICATES_LIST_SIZE = 50

write_files = True
most_recent_calls = []  # this is used to help prevent duplicate records.
missing_destinations = []

# this is a terrible hack to get some cruft out of the brandmeister talk group names.

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
        dt = datetime.datetime.fromtimestamp(s, tz=datetime.timezone.utc)
        return dt.isoformat()
    except ValueError as e:
        logging.error(exc_info=e)
        # print(e)
        return None


sio = socketio.Client()


@sio.event
def connect():
    logging.info('connected')


@sio.on('mqtt')
def mqtt(data):
    global most_recent_calls
    global missing_destinations
    global write_files
    calls_to_log = []
    raw_data = json.loads(data['payload'])
    try:
        if raw_data.get('Event', '').strip() == 'Session-Stop':
            destination_id = raw_data.get('DestinationID', -1)
            context_id = raw_data.get('ContextID', -1)
            if destination_id in INTERESTING_TALKGROUPS or context_id in interesting_peer_ids:
                #  print('len(last_ten)={}'.format(len(last_ten)))
                if raw_data in most_recent_calls:
                    logging.debug('duplicate!' + str(raw_data))
                else:
                    if destination_id not in talk_group_number_to_name_dict:
                        if destination_id not in missing_destinations:
                            missing_destinations.append(destination_id)
                            logging.warning('cannot lookup destination id {}'.format(destination_id))

                    most_recent_calls.insert(0, raw_data)
                    if len(most_recent_calls) > DUPLICATES_LIST_SIZE:
                        most_recent_calls = most_recent_calls[:DUPLICATES_LIST_SIZE]
                    start = safe_int(raw_data.get('Start', '0'))
                    end = safe_int(raw_data.get('Stop', '0'))
                    elapsed = end - start
                    destination_name = raw_data.get('DestinationName', '').strip()

                    if destination_name not in talk_group_alias_to_number_dict['Brandmeister']:
                        old_destination_name = destination_name
                        destination_name = talk_group_network_number_to_name_dict['Brandmeister'].get(destination_id,
                                                                              '({})'.format(destination_id))
                        #destination_name = talk_group_number_to_name_dict.get(destination_id,
                        #                                                      '({})'.format(destination_id))
                        logging.warning('could not find destination name "{}", will use "{}".'.format(old_destination_name,
                                                                                                       destination_name))

                    destination_name = destination_name.replace(' - 10 Minute Limit', '')
                    destination_name = tg_remap.get(destination_name, destination_name)
                    destination_id = raw_data.get('DestinationID', -1)
                    slot = raw_data.get('Slot', -1)
                    if slot == -1:
                        print(raw_data)
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
                        logging.debug(
                            'Kerchunk! start: {} end:{} elapsed: {} total_count: {} destination: {} sourcecall: {}'.format(
                                start, end, elapsed, total_count, destination_name, source_call))

                    call = {
                        'timestamp': convert_brandmeister_timestamp(end),
                        'site': link_name,
                        'dest': destination_name,
                        'dest_id': destination_id,  # NEW NEW NEW
                        'slot': slot,  # NEW NEW NEW
                        'peer_id': context_id,
                        'peer_callsign': link_call,
                        'peer_name': link_name,
                        'radio_id': source_id,
                        'radio_callsign': source_call,
                        'radio_username': source_name,
                        'duration': elapsed,
                        'sourcepeer': '{} -- {}'.format(link_call, context_id)
                    }

                    line = '{},{},{},{},{},{},{},{},{},{},{},{},{}'.format(convert_brandmeister_timestamp(end),
                                                                           link_name,
                                                                           slot,  # NEW NEW NEW
                                                                           destination_name,
                                                                           destination_id,  # NEW NEW NEW
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
                        logging.info(line)
                        if len(link_call) == 0 or len(link_name) == 0:
                            logging.warning('no link data')
                            logging.warning(str(raw_data))

    except KeyError as ke:
        logging.error('KeyError: ' + str(ke))
        logging.error(str(raw_data))

    if len(calls_to_log) > 0:
        append_logged_calls(LOGGED_CALLS_FILENAME, calls_to_log)
        calls_to_log = []


@sio.event
def disconnect():
    logging.info('disconnected')


def main():
    global write_files
    global most_recent_calls
    global missing_destinations
    logging.info('starting')
    write_files = True
    most_recent_calls = []
    missing_destinations = []
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == 'test':
            INTERESTING_TALKGROUPS.extend([310, 311, 312, 313, 314, 315, 316, 317, 318, 319])
            # INTERESTING_TALKGROUPS.append(3100)  # lots of traffic
            write_files = False
            logging.info('NOT writing files -- debug mode.')
            logging.basicConfig(level=logging.DEBUG)
            logging.root.level = logging.DEBUG
    sio.connect(url=URL, socketio_path=SIO_PATH, transports='websocket')
    sio.wait()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:{}',
                        level=logging.INFO,
                        stream=sys.stdout)
    logging.Formatter.converter = time.gmtime
    main()
