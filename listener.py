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
                line = '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s' % (stuff['timestamp'],
                                                          stuff['site'],
                                                          stuff['dest'],
                                                          stuff['peer_id'],
                                                          stuff['peer_callsign'],
                                                          stuff['peer_name'],
                                                          stuff['radio_id'],
                                                          stuff['radio_callsign'],
                                                          stuff['radio_username'],
                                                          stuff['duration'])
                datafile.write(line + '\n')


def format_call(calldata):
    return '{timestamp},{site},{dest},{peer_id},{peer_callsign},{peer_name},{radio_id},{radio_callsign},{radio_username},{duration}'.format(**calldata)


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
        url = 'http://cbridge.k4usd.org:42420/data.txt'

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
            # if False: # get current qsos in progress # don't care about these, historical is good enough.
            #     users = sections[0].split('\t')
            #     for user in users:
            #         qso = {}
            #         items = user.split('\013')
            #         for i in range(0, len(datalabels)):
            #             qso[datalabels[i]] = items[i]
            #         # print(qso)
            #         parse_call(qso)
            #         print(qso)
            #         log_call2(qso)
            #         print('--')
            #         qsos.append(qso)

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
        result['qsos'] = qsos
        result['calls'] = calls
        if updatenumber != 0:
            result['updatenumber'] = updatenumber
    return result


def convert_cbridge_timestamp(s):
    try:
        ss = s.split(' ')
        tm = ss[0][0:8]
        year = datetime.datetime.now().year
        dt = '{} {} {} {}'.format(tm, ss[1], ss[2], year)
        return datetime.datetime.strptime(dt, "%H:%M:%S %b %d %Y").isoformat()
    except ValueError as e:
        print(e)
        return None


def parse_call_data(call):
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

    stuff = call['sourcepeer'].split('--')
    if len(stuff) == 1:
        more_stuff = stuff[0].split('-')
        if len(more_stuff) == 1:
            call['peer_id'] = safe_int(more_stuff[0].strip())
            call['peer_callsign'] = 'n/a'
            call['peer_name'] = 'n/a'
        elif len(more_stuff) == 2:
            call['peer_id'] = 0
            call['peer_callsign'] = more_stuff[0].strip()
            call['peer_name'] = more_stuff[1].strip()
        else:
            call['peer_id'] = safe_int(stuff[0].strip())
            call['peer_callsign'] = '.'
            call['peer_name'] = '.'
    elif len(stuff) == 2:
        call['peer_id'] = safe_int(stuff[1].strip())
        more_stuff = stuff[0].split('-')
        if len(more_stuff) == 1:
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


def do_poll(update_number):
    params = {'param': 'ajaxcallwatch', 'url': 'http://cbridge.k4usd.org:42420/data.txt'}
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
    update_number = 0
    seen_talk_groups_filename = 'seen_talk_groups.txt'
    logged_calls_filename = 'logged_calls.txt'
    update_interval = 15
    seen_talk_groups = read_seen_talk_groups(seen_talk_groups_filename)

    write_files = True

    while True:
        calls, update_number = do_poll(update_number)
        new_talk_groups = set()
        calls_to_log = []
        ignored_calls = []
        for call in calls:
            # print(call)
            fdest = call['filtered_dest']
            # if fdest.startswith('UnKnown'):
            #    ignored_calls.append(call)
            #    continue
            if fdest not in seen_talk_groups and fdest not in new_talk_groups:
                new_talk_groups.add(fdest)
                print("new talk group: %s" % fdest)
            if fdest in interesting_talk_group_names or call['peer_id'] in interesting_peer_ids:
                calls_to_log.append(call)
                # print_call(call)
            else:
                ignored_calls.append(call)
        if len(new_talk_groups) > 0:
            seen_talk_groups = seen_talk_groups.union(new_talk_groups)
            if write_files:
                write_seen_talk_groups(seen_talk_groups_filename, sorted(seen_talk_groups))

        if write_files:
            append_logged_calls(logged_calls_filename, calls_to_log)
        if len(calls_to_log):
            for call in calls_to_log:
                s = format_call(call)
                logging.info(s)
        if False:
            if len(ignored_calls):
                for call in ignored_calls:
                    s = format_call(call)
                    logging.info('not logged: ' + s)
        logging.debug("logged %d, ignored %d, update # %d" % (len(calls_to_log), len(ignored_calls), update_number))
        time.sleep(update_interval)


if __name__ == '__main__':
    main()
