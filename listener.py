#!/bin/python3
#
import datetime
import logging
import urllib
import urllib.parse
import urllib.request
import sys
import time

from common import interesting_talk_group_names
# from common import uninteresting_talk_group_names
from common import interesting_peer_ids
from common import filter_talk_group_name

DATA_URL = 'http://w0yc.stu.umn.edu:42420/data.txt'

logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
logging.Formatter.converter = time.gmtime


def safe_int(s):
    try:
        return int(s)
    except ValueError:
        return -1


def read_seen_talk_groups(filename):
    talk_groups = set()
    try:
        with open(filename, 'r') as datafile:
            for line in datafile:
                talk_groups.add(line.strip())
    except FileNotFoundError:
        pass
    return talk_groups


def append_seen_talk_groups(filename, new_group_list):
    if new_group_list is not None and len(new_group_list) > 0:
        with open(filename, 'a') as datafile:
            for group_name in new_group_list:
                datafile.write(group_name + '\n')


def write_seen_talk_groups(filename, group_list):
    if group_list is not None and len(group_list) > 0:
        with open(filename, 'w') as datafile:
            for group_name in group_list:
                datafile.write(group_name + '\n')


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


def format_call(calldata):
    return '{timestamp},{site},{dest},{peer_id},{peer_callsign},{peer_name},{radio_id},{radio_callsign},{radio_username},{duration}'.format(
        **calldata)


def print_call(stuff):
    """
    print the call data, csv style
    now obsolete
    :param stuff: the dict of the call data
    :return: None
    """
    try:
        print(format_call(stuff), flush=True)
    except Exception as e:
        print('** failed to parcel call dict **')
        print(e)
        print(stuff)


def call_cbridge(**params):
    datalabels = ['time', 'duration', 'sourcepeer', 'sourceradio', 'dest', 'rssi', 'site', 'lossrate']
    logging.debug('Calling cbridge')
    qsos = []
    calls = []
    updatenumber = 0
    result = {'updatenumber': 0, 'qsos': [], 'calls': []}
    if params.get('url'):
        url = params.pop('url')
    else:
        url = DATA_URL

    data = urllib.parse.urlencode(params)
    req = urllib.request.Request(url + '?' + data,
                                 headers={'User-Agent': 'N1KDO c-bridge scraper, contact n1kdo to make it stop.'})
    response = urllib.request.urlopen(req)
    for line in response:
        try:
            line = line.decode('iso-8859-1')
            line = line.replace('&nbsp;', ' ')
            line = line.replace(',', '_')
            sections = line.split('\010')
            stuff = sections[1].split('\t')
            for s in stuff:
                sections = s.split('\013')
                if len(sections) == 1:
                    updatenumber = sections[0]
                else:
                    call = {}
                    if len(sections) != len(datalabels):
                        print('something is not right!')
                        print(stuff)
                        print(sections)
                        print('---')
                    for i in range(0, len(datalabels)):
                        if datalabels[i] == 'duration':
                            try:
                                d = str(float(sections[i]))
                            except Exception as e:
                                print(e)
                                print(sections)
                                sections[i] = '0.0'
                        call[datalabels[i]] = sections[i]
                    parse_call_data(call)
                    calls.append(call)
        except Exception as ex:
            print()
            print('...problem')
            print(line)
            e = sys.exc_info()[0]
            print('Problem with web query:')
            print(e)
            print(ex)
        result['qsos'] = qsos
        result['calls'] = calls
        if updatenumber != 0:
            result['updatenumber'] = updatenumber
    return result


month_name_to_number_dict = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                             'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}


def convert_cbridge_timestamp(s):
    try:
        ss = s.split(' ')
        tm = ss[0][0:8]
        year = datetime.datetime.now().year
        month = month_name_to_number_dict.get(ss[1][:3].lower(), -1)
        day = safe_int(ss[2])
        zone = '-0500'
        dt = '{:4d}-{:02d}-{:02d}T{}{}'.format(year, month, day, tm, zone)
        #return dt
        # dy = datetime.datetime.fromisoformat(dt)
        dy = datetime.datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S%z')
        dx = dy.astimezone(tz=datetime.timezone.utc)
        return dx.isoformat()
        #ts = datetime.datetime.strptime('%Y-%m-%dT%H:%M:%S%z', dt)
        #return dt
        #return ty.isoformat()
    except ValueError as e:
        print(e)
        return None


def parse_call_data(call):
    #print(call)
    call['timestamp'] = convert_cbridge_timestamp(call['time'])
    call['filtered_dest'] = filter_talk_group_name(call['dest'])
    call['radio_callsign'] = ''
    call['radio_username'] = ''
    call['radio_id'] = 0
    stuff = call['sourceradio'].split('--')
    if len(stuff) == 1:
        call['radio_id'] = safe_int(stuff[0].strip())
        call['radio_callsign'] = 'N/A'
        call['radio_username'] = 'N/A'
    elif len(stuff) == 2:
        call['radio_id'] = stuff[1].strip()
        more_stuff = stuff[0].split('-')
        if len(more_stuff) == 3:
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

    if False:
        logging.debug(
            'sourceradio stuff: {}, radio_id: {}, radio_callsign: {}, radio_username: {}'.format(str(stuff),
                                                                                          call['radio_id'],
                                                                                          call['radio_callsign'],
                                                                                          call['radio_username']))

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
    if False:
        logging.debug('sourcepeer stuff: {} peer_id: {}, peer_callsign: {}, peer_name: {}'.format(str(stuff),
                                                                                                  call['peer_id'],
                                                                                                  call['peer_callsign'],
                                                                                                  call['peer_name']))
    #if call['peer_id'] == 'n/a':
    #    logging.warning(str(call))
    # print(call)


def do_poll(update_number):
    params = {'param': 'ajaxcallwatch', 'url': DATA_URL}
    if update_number != 0:
        params['updatenumber'] = '%d' % update_number
    try:
        result = call_cbridge(**params)
        calls = []
        if result is not None:
            if update_number > 0:
                calls = result['calls']
            update_number = int(result['updatenumber'])
        return calls, update_number
    except Exception as e:
        print(e)
        return [], update_number


def main():
    #
    # main part....
    #
    write_files = True
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == 'test':
            write_files = False
            #logging.basicConfig(level=logging.INFO)
            logging.basicConfig(level=logging.DEBUG)
            logging.root.level = logging.DEBUG

    update_number = 0
    seen_talk_groups_filename = 'seen_talk_groups.txt'
    logged_calls_filename = 'logged_calls.txt'
    update_interval = 30
    seen_talk_groups = read_seen_talk_groups(seen_talk_groups_filename)
    next_poll = int(time.time())

    while True:
        calls, update_number = do_poll(update_number)
        new_talk_groups = set()
        calls_to_log = []
        ignored_calls = []
        for call in calls:
            # print(call)
            fdest = call['filtered_dest']
            peer_id = call.get('peer_id') or -1
            # if fdest.startswith('UnKnown'):
            #    ignored_calls.append(call)
            #    continue
            if fdest not in seen_talk_groups and fdest not in new_talk_groups and not fdest.lower().startswith(
                    'unknown'):
                new_talk_groups.add(fdest)
                print("new talk group: %s" % fdest)
            if fdest in interesting_talk_group_names or peer_id in interesting_peer_ids:
                calls_to_log.append(call)
            else:
                ignored_calls.append(call)
        if len(new_talk_groups) > 0:
            seen_talk_groups = seen_talk_groups.union(new_talk_groups)
            if write_files:
                write_seen_talk_groups(seen_talk_groups_filename, sorted(seen_talk_groups))

        if write_files:
            append_logged_calls(logged_calls_filename, calls_to_log)
        else:
            if len(calls_to_log):
                for call in calls_to_log:
                    s = format_call(call)
                    logging.info('logging  : {}'.format(s))
        if not write_files:
            if len(ignored_calls):
                for call in ignored_calls:
                    s = format_call(call)
                    logging.info('not logged: ' + s)
                    # logging.info(str(call))
        logging.debug("logged %d, ignored %d, update # %d" % (len(calls_to_log), len(ignored_calls), update_number))
        next_poll = next_poll + update_interval
        try:
            while time.time() < next_poll:
                time.sleep(1)
        except KeyboardInterrupt as e:
            print('\nexiting...\n')
            exit(0)


if __name__ == '__main__':
    main()
