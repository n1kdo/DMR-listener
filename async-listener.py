#!/bin/python3

import datetime
import json
import asyncio
import aiohttp
import socketio
import sys
import logging
import time

import common
from common import filter_talk_group_name
from common import interesting_peer_ids
from common import interesting_talk_groups
from common import less_interesting_talk_groups
from common import interesting_talk_group_names
from common import less_interesting_talk_group_names
from common import talk_group_alias_to_number_dict
from common import talk_group_number_to_name_dict
from common import talk_group_network_number_to_name_dict

URL = 'https://api.brandmeister.network'
SIO_PATH = '/lh/socket.io'

# CBRIDGE_CALL_WATCH_API = 'http://w0yc.stu.umn.edu:42420/data.txt'  # K4USD with nobody on it
# CBRIDGE_SITE = 'K4USD Network'
#CBRIDGE_CALL_WATCH_API ='https://cbridge.hamdigital.net/data.txt'  # hamdigital atl
CBRIDGE_CALL_WATCH_API = 'https://cbridge-scraper.hamdigital.net/data.txt'  # hamdigital atl
CBRIDGE_SITE = 'Ham Digital'

LOGGED_CALLS_FILENAME = 'async_logged_calls.txt'
DUPLICATES_LIST_SIZE = 50

write_files = True
most_recent_calls = []  # this is used to help prevent duplicate records.
missing_destinations = []

repeaters = []
repeaters_by_id = {}

run_cbridge_poller = True

# this is a terrible hack to get some cruft out of the brandmeister talk group names.


def validate_call_data(call):
    # print(call)
    dest_id = call.get('dest_id')
    call_talk_group_name = call.get('filtered_dest') or call.get('dest') or '!no_dest!'
    if call_talk_group_name[0] == '(' and call_talk_group_name[-1] == ')':
        #logging.warning(f'Not a talk group name: {call_talk_group_name}, dest_id: {call.get("dest_id")}')
        return False
    if 'Unknown Ipsc' in call_talk_group_name:
        return False
    site = call.get('site') or '!no site!'
    network_name = common.site_name_to_network_map.get(site)
    if network_name is None:
        logging.warning(f'No network for site {site} {call}')
        return False
    network_talk_groups = common.talk_groups.get(network_name)
    if network_talk_groups is None:
        logging.warning(f'No talk groups for network {network_name} {call}')
        return False
    found_talk_group = None
    for talk_group in network_talk_groups:
        if talk_group.get('name') == call_talk_group_name:
            found_talk_group = talk_group
            break
    if found_talk_group is None:
        logging.warning(f'Cannot find talk group {call_talk_group_name} in network {network_name} {call}')
        return False

    if dest_id is None:
        dest_id = found_talk_group.get('tg')
        call['dest_id'] = dest_id
        logging.info(f'Added dest_id {dest_id}')
    else:
        if found_talk_group.get('tg') != dest_id:
            logging.warning(f'Confused! dest_id {dest_id} does not match found tg: {found_talk_group} in call {call}')
            call['dest'] = f'({dest_id})'

    if dest_id is not None:
        peer_id = call.get('peer_id')
        if peer_id is not None:
            repeater = repeaters_by_id.get(peer_id)
            if repeater is not None:
                # print(f'found repeater {repeater}')
                repeater_talk_groups = repeater.get('talk_groups')
                if repeater_talk_groups is not None:
                    found_talk_group = None
                    for talk_group in repeater_talk_groups:
                        if dest_id == talk_group.get('talkgroup'):
                            # print(f'found matching talk group {talk_group}')
                            found_talk_group = talk_group
                    if found_talk_group is not None:
                        found_slot = found_talk_group.get('slot')
                        slot = call.get('slot')
                        # print(f'found_slot {found_slot}, slot {slot}')
    return found_talk_group is not None


def append_logged_calls(filename, calls):
    if calls is not None and len(calls) > 0:
        if write_files:
            with open(filename, 'a') as outfile:
                for call in calls:
                    line = f"{call['timestamp']},{call['site']},{call['dest']},{call['peer_id']}," \
                           f"{call['peer_callsign']},{call['peer_name']},{call['radio_id']}," \
                           f"{call['radio_callsign']},{call['radio_username']},{call['duration']}," \
                           f"{call['sourcepeer']},{call.get('dest_id') or 0},{call.get('slot') or 0}"

                    outfile.write(line + '\n')
                    # print(line)
        else:
            for call in calls:
                line = f"{call['timestamp']},{call['site']},{call['dest']},{call['peer_id']}," \
                       f"{call['peer_callsign']},{call['peer_name']},{call['radio_id']}," \
                       f"{call['radio_callsign']},{call['radio_username']},{call['duration']}," \
                       f"{call['sourcepeer']},{call.get('dest_id') or 0},{call.get('slot') or 0}"
                print(f'not writing: {line}')


def safe_int(s, default=-1):
    if isinstance(s, int):
        return s
    try:
        return int(s)
    except ValueError:
        return default


def convert_brandmeister_timestamp(s):
    try:
        dt = datetime.datetime.fromtimestamp(s, tz=datetime.timezone.utc)
        return dt.isoformat()
    except ValueError as e:
        logging.error('bad timestamp', exc_info=e)
        # print(e)
        return None


sio = socketio.AsyncClient()


@sio.event
async def connect():
    logging.info('connected')


@sio.on('mqtt')
async def mqtt(data):
    global most_recent_calls
    global missing_destinations
    global write_files
    calls_to_log = []
    raw_data = json.loads(data['payload'])
    try:
        if raw_data.get('Event', '').strip() == 'Session-Stop':
            destination_id = raw_data.get('DestinationID', -1)
            context_id = raw_data.get('ContextID', -1)
            if destination_id in common.interesting_talk_groups or context_id in interesting_peer_ids:
                #  print('len(last_ten)={}'.format(len(last_ten)))
                if raw_data in most_recent_calls:
                    logging.debug('duplicate!' + str(raw_data))
                else:
                    if destination_id < 999999 and destination_id not in talk_group_number_to_name_dict:
                        if destination_id not in missing_destinations:
                            missing_destinations.append(destination_id)
                            logging.warning(f'Cannot lookup destination id {destination_id}')

                    most_recent_calls.insert(0, raw_data)
                    if len(most_recent_calls) > DUPLICATES_LIST_SIZE:
                        most_recent_calls = most_recent_calls[:DUPLICATES_LIST_SIZE]
                    start = safe_int(raw_data.get('Start', '0'))
                    end = safe_int(raw_data.get('Stop', '0'))
                    elapsed = float(end - start)
                    total_count = raw_data.get("TotalCount") or 0
                    #  guess_count = int(elapsed * 16.6667)
                    duration = round(total_count * 0.06, 1)  # guesstimate
                    #  print(f'elapsed={elapsed}, total_count={total_count}, guess_count={guess_count}, duration={duration}')
                    if duration != 0:
                        elapsed = duration

                    destination_name = raw_data.get('DestinationName', '!missing!').strip()
                    if destination_name not in talk_group_alias_to_number_dict['Brandmeister']:
                        old_destination_name = destination_name
                        destination_name = talk_group_network_number_to_name_dict['Brandmeister'].get(destination_id, f'({destination_id})')
                        logging.info(f'Could not find destination name "{old_destination_name}", will use "{destination_name}".')

                    slot = raw_data.get('Slot', -1)
                    if slot == -1:
                        logging.warning(raw_data)
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
                        'timestamp': convert_brandmeister_timestamp(start),
                        'site': 'Brandmeister',  # because this is all of brandmeister here...
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
                    if len(link_call) == 0 or len(link_name) == 0:
                        logging.debug(f'no link data {str(raw_data)}')
                    else:
                        # test the call here, do not want to log traffic from a C-Bridge
                        if link_name == 'CBridge CC-CC Link' and context_id == 111311:
                            logging.info(f'Not logging {link_name} traffic for call from peer {link_call} {context_id}')
                        else:
                            validate_call_data(call)
                            calls_to_log.append(call)

    except KeyError as ke:
        logging.error('KeyError: ' + str(ke))
        logging.error(str(raw_data))

    if len(calls_to_log) > 0:
        append_logged_calls(LOGGED_CALLS_FILENAME, calls_to_log)


@sio.event
async def disconnect():
    logging.info('disconnected')


# CBridge stuff
month_name_to_number_dict = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                             'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}


def convert_cbridge_timestamp(s):
    try:
        ss = s.split(' ')
        if len(ss) < 3:
            print(f'oopsy. s={s}')
            return None
        tm = ss[0][0:8]
        year = datetime.datetime.now().year
        month = month_name_to_number_dict.get(ss[1][:3].lower(), -1)
        day = safe_int(ss[2])
        zone = '-0000'
        dt = '{:4d}-{:02d}-{:02d}T{}{}'.format(year, month, day, tm, zone)
        # return dt
        # dy = datetime.datetime.fromisoformat(dt)
        dy = datetime.datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S%z')
        dx = dy.astimezone(tz=datetime.timezone.utc)
        return dx.isoformat()

    except ValueError as e:
        print(e)
        return None


def parse_cbridge_call_data(call):
    # print(call)
    call['timestamp'] = convert_cbridge_timestamp(call['time'])
    filtered_dest = filter_talk_group_name(call['dest'])
    call['filtered_dest'] = filtered_dest
    call['radio_callsign'] = ''
    call['radio_username'] = ''
    call['radio_id'] = 0
    stuff = call['sourceradio'].split('--')
    if len(stuff) == 1:
        call['radio_id'] = safe_int(stuff[0].strip())
        call['radio_callsign'] = 'N/A'
        call['radio_username'] = 'N/A'
    elif len(stuff) == 2:
        call['radio_id'] = safe_int(stuff[1].strip())
        more_stuff = stuff[0].split('-')
        l = len(more_stuff)
        if l == 3:
            call['radio_callsign'] = more_stuff[0].strip()
            call['radio_username'] = more_stuff[1].strip()
        elif l == 4:
            call['radio_callsign'] = more_stuff[0].strip()
            call['radio_username'] = more_stuff[1].strip()
    elif len(stuff) == 3:
        call['radio_id'] = safe_int(stuff[2].strip())
        more_stuff = stuff[0].split('-')
        if len(more_stuff) == 3:
            call['radio_callsign'] = more_stuff[0].strip()
            call['radio_username'] = more_stuff[1].strip()
    elif len(stuff) == 4:
        call['radio_id'] = safe_int(stuff[3].strip())
        more_stuff = stuff[0].split('-')
        if len(more_stuff) == 3:
            call['radio_callsign'] = more_stuff[0].strip()
            call['radio_username'] = more_stuff[1].strip()
    else:
        print('=== len(stuff)=%d ===' % len(stuff))
        print(stuff)
        call['radio_id'] = safe_int(stuff[3].strip())
        more_stuff = stuff[0].split('-')
        if len(more_stuff) == 3:
            call['radio_callsign'] = more_stuff[0].strip()
            call['radio_username'] = more_stuff[1].strip()
        print(call)

    stuff = call['sourcepeer'].split('--')
    # logging.debug('sourcepeer stuff: ' + str(stuff))
    if len(stuff) == 1:
        more_stuff = stuff[0].split('-')
        # logging.debug('more_stuff: {} '.format(len(more_stuff)) + str(more_stuff))
        if len(more_stuff) == 1:
            call['peer_id'] = safe_int(more_stuff[0].strip())
            call['peer_callsign'] = 'n/a'
            call['peer_name'] = 'n/a'
        elif len(more_stuff) == 2:
            call['peer_id'] = 'n/a'
            callsign = more_stuff[0].strip()
            if callsign == 'BM':  # hack hack
                call['peer_callsign'] = stuff[0]
            else:
                call['peer_callsign'] = callsign
            call['peer_name'] = more_stuff[1].strip()
            if 'BM-' in call['peer_callsign']:
                call['peer_id'] = 0 - safe_int(call['peer_name'])  # non-cbridge peer ID
            if call['peer_name'] == 'HotSpot':
                even_more_stuff = call['site'].split('-')
                # logging.debug('even_more_stuff: {} : '.format(len(even_more_stuff)) + str(even_more_stuff))
                if len(even_more_stuff) == 3:
                    call['peer_id'] = 0 - safe_int(even_more_stuff[2])
        elif len(more_stuff) == 3:
            call['peer_id'] = more_stuff[2].strip()
            call['peer_callsign'] = more_stuff[0].strip()
            call['peer_name'] = more_stuff[1].strip()
        else:
            call['peer_id'] = safe_int(stuff[0].strip())
            call['peer_callsign'] = 'n/a'
            call['peer_name'] = 'n/a'
    elif len(stuff) == 2:
        peer_id = safe_int(stuff[1].strip())
        call['peer_id'] = peer_id
        more_stuff = stuff[0].split('-')
        if len(more_stuff) == 1:
            peer_name = more_stuff[0].strip()
            if peer_name == 'BM':
                call['peer_name'] = 'Brandmeister'
                if 393100 <= peer_id <= 393109:
                    call['peer_callsign'] = 'BM{}'.format(peer_id - 390000)
                else:
                    call['peer_callsign'] = 'n/a'
            else:
                call['peer_callsign'] = 'n/a'
                call['peer_name'] = more_stuff[0].strip()
        elif len(more_stuff) == 2:
            call['peer_callsign'] = more_stuff[0].strip()
            call['peer_name'] = more_stuff[1].strip()
        elif len(more_stuff) == 3:
            call['peer_callsign'] = more_stuff[0].strip().split(' ')[0]
            call['peer_name'] = more_stuff[1].strip() + more_stuff[2].strip()
        else:
            print('=== len(more_stuff)=%d ===' % len(more_stuff))
            print(more_stuff)
            call['peer_callsign'] = 'unknown'
            call['peer_name'] = 'unknown'
    else:
        call['peer_id'] = safe_int(call['sourcepeer'])


async def cbridge_poller():
    data_labels = ['time', 'duration', 'sourcepeer', 'sourceradio', 'dest', 'rssi', 'site', 'lossrate']
    update_number = 0
    headers = {'User-Agent': 'N1KDO C-Bridge scraper, contact n1kdo to make it stop.'}

    while run_cbridge_poller:
        calls = []
        if update_number > 0:
            url = f'{CBRIDGE_CALL_WATCH_API}?param=ajaxcallwatch&updatenumber={update_number}'
        else:
            url = f'{CBRIDGE_CALL_WATCH_API}?param=ajaxcallwatch'

        try:
            logging.info(f'polling {url}')
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as response:
                    status = response.status
                    if status != 200:
                        logging.warning(f'http get returned status {status}')
                    payload = await response.text('ISO-8859-1')
                    parts = payload.split('\t')
                    # logging.debug(f'got {len(parts)} rows of data...')
                    try:
                        for line in parts:
                            call = {}
                            line = line.replace('&nbsp;', ' ')
                            line = line.replace(',', '_')
                            sections = line.split('\010')
                            if len(sections) == 2:
                                # logging.debug(f'sections[1]={sections[1]}')
                                if update_number == 0:
                                    update_number = safe_int(sections[1])
                                    break  # do not collect call data from our first call to the cbridge
                                else:
                                    update_number = safe_int(sections[1])

                            sections = sections[0].split('\013')
                            if len(sections) != len(data_labels):
                                print('something is not right!')
                                print(sections)
                                print('---')
                                continue
                            if sections[0].strip() == '':
                                # logging.debug(f'empty row: {sections}')
                                continue
                            for i in range(0, len(data_labels)):
                                if data_labels[i] == 'duration':
                                    try:
                                        d = float(sections[i])
                                    except Exception as e:
                                        print(e)
                                        print(sections)
                                        d = 0.0
                                    call['duration'] = d
                                else:
                                    call[data_labels[i]] = sections[i]
                            parse_cbridge_call_data(call)
                            call_site = call.get('site') or 'missing'
                            call['call_site'] = call_site
                            call['site'] = CBRIDGE_SITE
                            if call_site[0:5].upper() not in ['BM-US', 'US-BM', 'BRAND']:
                                # print(f'allowed call_site={call_site}')
                                filtered_dest = call.get('filtered_dest') or 'missing'
                                peer_id = call.get('peer_id') or -1
                                if filtered_dest in interesting_talk_group_names or peer_id in interesting_peer_ids:
                                    validate_call_data(call)
                                    calls.append(call)

                    except RuntimeError as ex:  # Exception as ex:
                        print()
                        print('...problem')
                        print(line)
                        e = sys.exc_info()[0]
                        print('Problem with web query:')
                        print(e)
                        print(ex)
                        # raise ex
            logging.info(f'done polling, collected {len(calls)} calls')
            append_logged_calls(LOGGED_CALLS_FILENAME, calls)
        except aiohttp.client_exceptions.ClientConnectorError as exc:
            logging.error(f'error polling {url}: ', exc_info=exc)
        except Exception as e:
            logging.error(f'error polling {url}, {e}')
        await asyncio.sleep(30)
    logging.warning('cbridge poller exit...')


async def main():
    global run_cbridge_poller
    global write_files
    global most_recent_calls
    global missing_destinations
    global repeaters
    global repeaters_by_id
    logging.info('starting')
    write_files = True
    most_recent_calls = []
    missing_destinations = []
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == 'test':
            # interesting_talk_groups.extend(less_interesting_talk_groups)
            # interesting_talk_group_names.extend(less_interesting_talk_group_names)
            write_files = False
            logging.info('NOT writing files -- debug mode.')
            logging.basicConfig(level=logging.DEBUG)
            logging.root.level = logging.DEBUG

    with open('repeaters.json', 'rb') as repeaters_data_file:
        repeaters = json.load(repeaters_data_file)

    logging.info(f'loaded {len(repeaters)} repeaters from file.')
    for repeater in repeaters:
        repeaters_by_id[repeater['peer_id']] = repeater

    aloop = asyncio.get_event_loop()
    poller = None
    while run_cbridge_poller:
        if poller is not None:
            try:
                poller.cancel()
            except asyncio.CancelledError as cex:
                logging.exception('cancel failed', exc_info=cex)
        try:
            # uggh python 3.6 backwards compat
            poller = aloop.create_task(cbridge_poller())
            #poller = asyncio.create_task(cbridge_poller())

            await sio.connect(url=URL, socketio_path=SIO_PATH, transports='websocket')
            await sio.wait()
        except KeyboardInterrupt:
            run_cbridge_poller = False

        await sio.wait()
        if poller:
            await poller

    print('done')


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.WARNING,
                        stream=sys.stderr)
    logging.Formatter.converter = time.gmtime

    # uggh python 3.6 backwards compat
    loop = asyncio.new_event_loop()
    loop.run_until_complete(main())
    # asyncio.run(main())
