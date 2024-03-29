#!/bin/python3
import csv
import datetime
import json
import logging
import sys
import time

from common import talk_group_name_to_number_mapping, talk_group_number_to_data_mapping, site_name_to_network_map
from common import filter_talk_group_name

import charts


def convert_elapsed(elapsed):
    hours, remainder = divmod(elapsed, 3600)
    minutes, seconds = divmod(remainder, 60)
    hours, minutes, seconds = int(hours), int(minutes), int(seconds)
    if hours < 10:
        hours = '0%s' % int(hours)
    if minutes < 10:
        minutes = '0%s' % minutes
    if seconds < 10:
        seconds = '0%s' % seconds
    return '%s:%s:%s' % (hours, minutes, seconds)


def convert_iso_timestamp(s):
    if len(s) == 19:
        s += '+00:00'
    if sys.version_info[1] < 7 and len(s) == 25:
        # python 3.6 issue, %z cannot tolerate a colon in the zone offset.
        s = s[0:20] + '0000'
    try:
        return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S%z')
    except ValueError as ve:
        print('value error ' + str(ve))
        return None


def safe_int(s):
    try:
        return int(s)
    except ValueError:
        return -1


def read_file(filename):
    lines = []
    with open(filename, 'r') as f:
        lines = f.readlines()
    return lines


def read_log(filename, start, end):
    calls = []
    fields = ['timestamp', 'site', 'dest', 'peer_id', 'peer_callsign', 'peer_name',
              'radio_id', 'radio_name', 'radio_username', 'duration', 'source_peer', 'tgid', 'slot']

    rows = 0
    with open(filename, 'r') as datafile:
        csvreader = csv.DictReader(datafile, fields)
        for row in csvreader:
            rows += 1
            tss = row.get('timestamp')
            if tss is None:
                continue
            ts = convert_iso_timestamp(tss)
            if ts is not None:
                row['timestamp'] = ts
                if start is not None and ts < start or end is not None and ts > end:
                    continue

            duration = row.get('duration') or '0'
            if duration is not None:
                try:
                    row['duration'] = float(duration)
                except Exception as e:
                    print(e)
                    print(row)
            else:
                row['duration'] = 0.0
            if row.get('peer_id') is not None:
                row['peer_id'] = safe_int(row['peer_id'])
            if row.get('radio_id') is not None:
                row['radio_id'] = safe_int(row['radio_id'])
            calls.append(row)

    logging.info('read        {} rows'.format(rows))
    logging.info('filtered to {} records'.format(len(calls)))
    return calls


def write_csv_contacts(users):
    """
    write a CSV file that is compatible with N0GSG contacts input
    :param users: a list of users
    :return: None
    """
    filename = 'contacts.csv'
    with open(filename, 'w') as datafile:
        for user in users:
            line = '"%s","%s","Private Call", "No","","","","",""' % (user['radio_id'],
                                                                      user['radio_name'] + ' ' + user['radio_username'])
            datafile.write(line + '\n')


def write_csv_moto_contacts(users):
    """
    write a CSV file that is compatible with moto contacts input
    :param users: a list of users
    :return: None
    """
    filename = 'moto_contacts.csv'
    with open(filename, 'w') as datafile:
        datafile.write("Name,radio_id\n")
        for user in users:
            line = '"%s","%s"' % (user['radio_name'], user['radio_id'])
            datafile.write(line + '\n')


def write_repeater_html(repeaters, filename='repeaters.html'):
    """
    write data for web
    :return:
    """
    header_lines = read_file('log_analytics_fragment.html')
    title = 'Selected Georgia DMR Repeaters'
    now = datetime.datetime.now()
    disclaimer = f'Generated {now.strftime("%Y-%m-%d %H:%M")}<br>Corrections and suggestions are appreciated.'
    copying = 'This data was collected and is maintained by hand by N1KDO.  Please do not reproduce it without attribution.'
    with open(filename, 'w') as htmlfile:
        htmlfile.write('<html lang="i-klingon">\n<head>\n')
        htmlfile.write('<title>' + title + '</title>\n')
        if header_lines is not None:
            htmlfile.writelines(header_lines)
        htmlfile.write("""
  <meta name="viewport" content="width=device-width, initial-scale=0.75">      
  <style>
BODY {
    background-color: #2c3e50;
    color: white;
    margin: 0;
    border: 0;
    font-family: sans-serif;
}
TABLE, TH, TR, TD {
    border: solid black 1px; 
    color: black;
}
.talk-groups-table {
    background-color: #cfc;
    border-collapse: collapse;
    font-size: 0.8em;
    margin-left: auto;
    margin-right: auto;
}
.tg-name {
    text-align: left;
}
.tg-number {
    text-align: right;
}
.tabs {
    overflow: hidden;
    box-shadow: 0 4px 4px -2px rgba(0, 0, 0, 0.5);
}
.tab {
    width: 100%;
    color: white;
    overflow: hidden;
}
.tab-label {
    display: -webkit-box;
    display: flex;
    -webkit-box-pack: justify;
    justify-content: space-between;
    padding: 1em;
    background: #2c3e50;
    font-weight: bold;
    cursor: pointer;
}
.tab-label:hover {
    background: #1a252f;
}
.tab-label::after {
    content: ">";
    width: 1em;
    height: 1em;
    text-align: center;
    -webkit-transition: all .35s;
    transition: all .35s;
}
.tab-content {
    background-color: #233;
    max-height: 0;
    padding: 0 1em;
    color: black;
    -webkit-transition: all .35s;
    transition: all .35s;
}
input:checked + .tab-label {
    background: black;
}
input:checked + .tab-label::after {
    -webkit-transform: rotate(90deg);
    transform: rotate(90deg);
}
input:checked ~ .tab-content {
    max-height: 200vh;
    padding: 1em;
}
input {
    position: absolute;
    opacity: 0;
    z-index: -1;
}
.heading {
    text-align: center;
    font-size: 2em;
    font-weight: bold;
}
.copying {
    text-align: center;
    font-size: 1em;
    color: #ff0;
}
.disclaimer {
    font-size: 1em;
    text-align: center;
}
.notes {
    font-size: 1em;
    text-align: center;
    color: #ff8;
}
.rptr-last-heard {
    font-size: 1em;
    text-align: center;
color: black;
}
.rptr-not-heard {
    color: red;
    font-weight: bold;
}
  </style>
""")
        htmlfile.write('</head>\n<body>\n')
        htmlfile.write('<div class="heading">' + title + '</div>\n')
        htmlfile.write('<div class="disclaimer">' + disclaimer + '</div>\n')
        htmlfile.write('<div class="copying">' + copying + '</div>\n')
        htmlfile.write('<div class="tabs">\n')
        ctr = 1
        sorted_repeaters = sorted(repeaters, key=lambda repeater: repeater['call'])
        for repeater in sorted_repeaters:
            last_heard = repeater.get('last_heard')
            notes = repeater.get('notes')
            if last_heard is None and notes is None:
                logging.warning(f'Not reporting repeater {repeater["peer_id"]} {repeater["call"]} because it has not been seen.')
                continue
            htmlfile.write('<div class="tab">\n')
            htmlfile.write('<input type="checkbox" id="chck{}">\n'.format(ctr))
            rptr = '{} {} {}'.format(repeater['call'], repeater['output'], repeater['location'])
            htmlfile.write('<label class="tab-label" for="chck{}">{}</label>\n'.format(ctr, rptr))
            htmlfile.write('<div class="tab-content">\n')
            htmlfile.write('<table class="talk-groups-table">\n')
            info = '{} {} {} {} CC {} {}'.format(repeater['call'], repeater['location'], repeater['output'], repeater['input'], repeater['color_code'], repeater['network'])
            htmlfile.write('<tr><th colspan="4" class="rptr-info">{}</th></tr>\n'.format(info))
            if last_heard is not None:
                last_heard = 'Last Heard ' + last_heard.strftime("%Y-%m-%d %H:%M:%S")
                htmlfile.write(f'<tr><th colspan="4" class="rptr-last-heard">{last_heard}</th></tr>\n')
            else:
                htmlfile.write(f'<tr><th colspan="4" class="rptr-not-heard">Not Heard</th></tr>\n')
            talk_groups = sorted(repeater['talk_groups'], key=lambda item: item['talkgroup'])
            htmlfile.write('<tr><th>Talk Group Name</th><th>TG #</th><th>TS #<br>#</th><th>Notes</th></tr>\n')
            for ts in [1, 2]:
                for talk_group in talk_groups:
                    tg_number = safe_int(talk_group['talkgroup'])
                    tg_timeslot = talk_group['slot']
                    tg_mode = talk_group['mode']
                    talk_group_data = talk_group_number_to_data_mapping[repeater['network']].get(tg_number)
                    if talk_group_data is None:
                        if tg_number < 99999:
                            logging.warning(f'missing talk group data for tg {tg_number} on peer {repeater["peer_id"]} network {repeater["network"]}')
                        talk_group_data = {'description': f'Unknown talk group {tg_number}', 'tg': str(tg_number)}
                    if tg_timeslot == ts:
                        if tg_mode == 0:
                            mode = 'static'
                        else:
                            mode = ''
                        htmlfile.write(f'<tr><td class="tg-name">{talk_group_data["description"]}</td><td class="tg-number">{tg_number}</td><td class="tg-number">{tg_timeslot}</td><td class="tg-number">{mode}</td></tr>\n')
            htmlfile.write('</table>\n')

            if notes is not None:
                htmlfile.write('<p class="notes">{}</p>\n'.format(notes))
            htmlfile.write('</div>\n')
            htmlfile.write('</div>\n')
            ctr += 1
        htmlfile.write('</div>\n')
        htmlfile.write('<div class="copying">' + copying + '</div>\n')
        htmlfile.write('</body></html>\n')


def write_peers_html(peers_list, heading='', filename='peers.html'):
    header_lines = read_file('log_analytics_fragment.html')
    with open(filename, 'w') as htmlfile:
        htmlfile.write('<html lang="i-klingon">\n<head>\n')
        htmlfile.write('<title>' + heading + '</title>\n')
        if header_lines is not None:
            htmlfile.writelines(header_lines)
        htmlfile.write("""
<meta name="viewport" content="width=device-width, initial-scale=0.75">
<style>
BODY {
    margin: 0;
    border: 0;
    font-family: sans-serif;
}
.peers-table {
    border-collapse: collapse;
    font-size: 0.8em;
    margin-left: auto;
    margin-right: auto;
}
.header-row {
    background-color: #ccc;
}
.peer-row {
    background-color: #cfc;
}
.talkgroup-row {
    background-color: #cff;
}
TABLE, TH, TD {
    border: solid black 1px;
    padding: 2px
}
.right {
    text-align:right;
}
.heading {
    text-align:center;
    font-size: 1.5em;
    font-weight: bold;
}
  </style>
</head>
""")
        htmlfile.write('<body>\n')
        htmlfile.write('<p class="heading">' + heading + '</p>\n')
        htmlfile.write('<div>\n')
        htmlfile.write('<table class="peers-table">\n')
        htmlfile.write('<tr class="header-row"><th>Peer ID</th><th>Callsign</th><th>Peer Name</th><th>Count</th><th>Elapsed</th><th>Last Heard UTC</th></tr>\n')
        for peer in peers_list:
            peer_id = peer['peer_id']
            peer_id_int = safe_int(peer_id)
            if 0 < peer_id_int < 1000000:
                htmlfile.write('<tr class="peer-row">')
                if peer_id > 0:
                    peer_str = '{:6d}'.format(peer_id)
                else:
                    peer_str = peer.get('peer_name') or 'unknown'
                htmlfile.write('<td class="right">{}</td>'.format(peer_str))
                htmlfile.write('<td>' + peer['peer_callsign'] + '</td>')
                htmlfile.write('<td>' + peer['peer_name'] + '</td>')
                htmlfile.write('<td class="right">' + str(peer['count']) + '</td>')
                htmlfile.write('<td>' + convert_elapsed(peer['total_elapsed']) + '</td>')
                htmlfile.write('<td>{:%Y-%m-%d %H:%M}</td>'.format(peer['last_heard']))
                htmlfile.write('</tr>\n')
                peer_talk_groups = peer['talk_groups']
                all_talk_groups = list(peer_talk_groups.values())
                sorted_talk_groups = sorted(all_talk_groups, key=lambda tg: tg['total_elapsed'], reverse=True)
                # sorted_talk_groups = sorted(all_talk_groups, key=lambda tg: tg['talk_group_number'])
                for talk_group in sorted_talk_groups:
                    # print(talk_group['talk_group'])
                    if talk_group['talk_group'].lower().startswith('unknown'):
                        continue
                    htmlfile.write('<tr class="talkgroup-row">')
                    htmlfile.write('<td colspan="2" class="right">{:6d}</td>'.format(talk_group['talk_group_number']))
                    htmlfile.write('<td>{:s}</td>'.format(talk_group['talk_group']))
                    htmlfile.write('<td class="right">{:5d}</td>'.format(talk_group['count']))
                    htmlfile.write('<td>' + convert_elapsed(talk_group['total_elapsed']) + '</td>')
                    htmlfile.write('<td>{:%Y-%m-%d %H:%M}</td>'.format(talk_group['last_heard']))
                    htmlfile.write('</tr>\n')
        htmlfile.write('</table>\n')
        htmlfile.write('</div>\n')
        htmlfile.write('</body></html>\n')


def validate_repeater_data(repeaters_list, peers_list):
    logging.info('validating repeater data...')
    for peer in peers_list:
        peer_id = peer['peer_id']
        if 310000 <= peer_id <= 319999:
            repeater_found = False
            for repeater in repeaters_list:
                if int(repeater['peer_id']) == peer_id:
                    if repeater['network'] != 'Brandmeister':
                        repeater_talk_groups = repeater['talk_groups']
                        peer_talk_groups = peer['talk_groups']
                        for peer_talk_group in peer_talk_groups:
                            ptgn = peer_talk_groups[peer_talk_group]['talk_group_number']
                            if ptgn < 1:
                                continue
                            talk_group_found = False
                            for repeater_talk_group in repeater_talk_groups:
                                rtgn = repeater_talk_group.get('talkgroup')
                                if ptgn == rtgn:
                                    talk_group_found = True
                            if not talk_group_found:
                                if ptgn != 16777215:
                                    logging.warning('Did not find matching tg {} on repeater {}'.format(ptgn, peer_id))
                    repeater_found = True
                    # print(f'peer_id={peer_id}, last_heard = {peer.get("last_heard")}')
                    repeater['last_heard'] = peer.get('last_heard')

            if not repeater_found:
                logging.warning(f'Could not find a repeater with peer_id {peer_id}')


def update_usage(a_dict, call):
    talk_group_name = call.get('dest')
    tgid = call.get('tgid') or '-1'
    talk_group_number = safe_int(tgid)
    timestamp = call['timestamp']
    duration = float(call.get('duration') or 0.0)

    usage_dict = a_dict['talk_groups'].get(talk_group_name)
    if usage_dict is None:
        usage_dict = {'talk_group': talk_group_name,
                      'count': 0,
                      'total_elapsed': 0,
                      'last_heard': None,
                      'talk_group_number': talk_group_number}
        a_dict['talk_groups'][talk_group_name] = usage_dict
    usage_dict['count'] += 1
    usage_dict['total_elapsed'] += duration
    usage_dict['last_heard'] = timestamp
    a_dict['last_heard'] = timestamp
    a_dict['count'] += 1
    a_dict['total_elapsed'] += duration


def update_peer(a_dict, call):
    peer_id = call.get('peer_id') or 0
    peer_callsign = call.get('peer_callsign')
    peer_name = call.get('peer_name')
    radio_id = call['radio_id'] or 0
    radio_name = call.get('radio_name') or 'unknown'
    #if peer_id == -1:
    #    if peer_callsign == radio_name:
    #        peer_id = radio_id
    #    peer_name = call.get('site') or 'unknown site'
    if peer_name == 'n/a':
        peer_name = call.get('site') or 'unknown site'
    if peer_callsign == 'n/a' and 310000000 < peer_id < 319999999:
        if int(peer_id/100) == radio_id:
            sub_peer = peer_id - radio_id * 100
            peer_callsign = '{}-{}'.format(radio_name, sub_peer)

    peer = a_dict.get(peer_id)
    if peer is None:
        peer = {'peer_id': peer_id,
                'peer_callsign': peer_callsign,
                'peer_name': peer_name,
                'count': 0,
                'total_elapsed': 0,
                'talk_groups': {},
                'last_heard': None,
                }
        a_dict[peer_id] = peer
    # update peer callsign to most recent
    peer['peer_callsign'] = peer_callsign
    peer['peer_name'] = peer_name
    update_usage(peer, call)


def print_peers(peers_list):
    print('%d Sources, sorted by elapsed time.' % len(peers_list))
    print()
    print('   Peer ID Callsign             Peer Name                        Count    Elapsed   Last Heard UTC ')
    print('---------- -------------------- ------------------------------   ----- ----------  ----------------')
    for peer in peers_list:
        print('{:10d} {:<20s} {:<30s} {:7d} {:>10s}  {:%Y-%m-%d %H:%M}'
              .format(peer['peer_id'], peer['peer_callsign'], peer['peer_name'],
                      peer['count'], convert_elapsed(peer['total_elapsed']), peer['last_heard']))
        peer_talk_groups = peer['talk_groups']
        all_talk_groups = list(peer_talk_groups.values())
        # sorted_talk_groups = sorted(all_talk_groups, key=lambda tg: tg['total_elapsed'], reverse=True)
        sorted_talk_groups = sorted(all_talk_groups, key=lambda tg: tg['talk_group_number'])
        for talk_group in sorted_talk_groups:
            if talk_group['talk_group'].startswith('UnKnown'):
                continue
            print('                                * {:6d} {:<20s} {:8d} {:>10s}  {:%Y-%m-%d %H:%M}'
                  .format(talk_group['talk_group_number'],
                          talk_group['talk_group'],
                          talk_group['count'],
                          convert_elapsed(talk_group['total_elapsed']),
                          talk_group['last_heard']))


def print_talkgroups(talkgroups_list):
    print('---------- talkgroups heard ----------')
    print('tg name          TG # count   elapsed ')
    print('------------ -------- ----- ----------')
    for tg in talkgroups_list:
        talk_group_data = talk_group_name_to_number_mapping['K4USD'].get(tg['talk_group'])
        if talk_group_data is None:
            talk_group_number = -1
        else:
            talk_group_number = talk_group_data['tg']
        print('%-12s %8d %5d %10s' % (tg['talk_group'],
                                      talk_group_number,
                                      tg['count'],
                                      convert_elapsed(tg['total_elapsed'])))


def print_users_detail1(users_list):
    print("%d users sorted by time usage" % len(users_list))
    print('Call    Name            Radio ID  Count     Time      Last Heard UTC ')
    print('------  --------------- --------  ----- ----------   ----------------')
    for user in users_list:
        print('{:<6s}  {:<15s} {:8d}  {:5d} {:>10s}   {:%Y-%m-%d %H:%M}'.format(user['radio_name'],
                                                                                user['radio_username'],
                                                                                user['radio_id'],
                                                                                user['count'],
                                                                                convert_elapsed(user['total_elapsed']),
                                                                                user['last_heard']))
        user_talk_groups = user['talk_groups']
        all_talk_groups = list(user_talk_groups.values())
        sorted_talk_groups = sorted(all_talk_groups, key=lambda tg: tg['total_elapsed'], reverse=True)
        # sorted_talk_groups = sorted(all_talk_groups, key=lambda tg: tg['talk_group_number'])
        for talk_group in sorted_talk_groups:
            print('* {:<24s} {:5d}  {:5d} {:>10s}   {:%Y-%m-%d %H:%M}'
                  .format(talk_group['talk_group'],
                          talk_group['talk_group_number'],
                          talk_group['count'],
                          convert_elapsed(talk_group['total_elapsed']),
                          talk_group['last_heard']))


def write_users_html(users_list, heading='', filename='users.html'):
    header_lines = read_file('log_analytics_fragment.html')
    with open(filename, 'w') as htmlfile:
        htmlfile.write('<html lang="i-klingon">\n<head>\n')
        htmlfile.write('<title>' + heading + '</title>\n')
        if header_lines is not None:
            htmlfile.writelines(header_lines)
        htmlfile.write("""
  <meta name="viewport" content="width=device-width, initial-scale=0.75">    
  <style>
BODY {
    margin: 0;
    border: 0;
    font-family: sans-serif;
}
.centered {
    text-align: center;
}
.users-table {
    border-collapse: collapse;
    font-size: 0.8em;
    margin-left: auto;
    margin-right: auto;
}
.user-row {
    background-color: #ccf;
}
.header-row {
    background-color: #ccc;
}
.peer-row {
    background-color: #cfc;
}
.peer-col-1 {
    padding-left: 2em;
}
.tg-row {
    background-color: #cff;
}
.tg-col-1 {
    padding-left: 4em;
}
.unknown-tg {
    color: red;
}
TABLE, TH, TD {
    border: solid black 1px;
    padding: 2px
}
.right {
    text-align: right;
}
.heading {
    text-align: center;
    font-size: 1.5em;
    font-weight: bold;
}
.subhead {
    text-align: center;
    font-size: 0.85em;
}
ul {
    display: table;
    font-size:0.85em;
    margin: 0 auto;
    text-align: left;
}
  </style>
</head>
""")
        htmlfile.write('<body>\n')
        htmlfile.write('<p class="heading">' + heading + '</p>\n')
        htmlfile.write('<p class="subhead">\n')
        htmlfile.write('Usage by user, sorted by total elapsed time.<br>\n')
        htmlfile.write('Users with low usage (count < 5, elapsed time < 10 seconds) are not shown on this report.\n')
        htmlfile.write('</p>\n')
        htmlfile.write('<div>\n')
        htmlfile.write('<table class="users-table">\n')
        htmlfile.write('<tr class="header-row"><th>Call</th><th>Name</th><th>Contact ID</th><th>Count</th><th>Elapsed</th><th>Last Heard UTC</th></tr>\n')
        for user in users_list:
            htmlfile.write('<tr class="user-row">')
            htmlfile.write('<td>{:s}</td>'.format(user['radio_name']))
            htmlfile.write('<td>{:s}</td>'.format(user['radio_username']))
            htmlfile.write('<td class="right">{:d}</td>'.format(user['radio_id']))
            htmlfile.write('<td class="right">{:d}</td>'.format(user['count']))
            htmlfile.write('<td>{:s}'.format(convert_elapsed(user['total_elapsed'])))
            htmlfile.write('<td>{:%Y-%m-%d %H:%M}</td>'.format(user['last_heard']))
            htmlfile.write('</tr>\n')

            user_peers = user['peers'] or {}
            all_peers = list(user_peers.values())
            sorted_peers = sorted(all_peers, key=lambda peer: peer['total_elapsed'], reverse=True)
            for peer in sorted_peers:
                htmlfile.write('<tr class="peer-row">')
                htmlfile.write('<td class="peer-col-1" colspan="2">{:s}</td>'.format(peer['peer_callsign']))
                htmlfile.write('<td class="right">{:d}</td>'.format(peer['peer_id']))
                htmlfile.write('<td class="right">{:d}</td>'.format(peer['count']))
                htmlfile.write('<td>{:s}'.format(convert_elapsed(peer['total_elapsed'])))
                htmlfile.write('<td>{:%Y-%m-%d %H:%M}</td>'.format(peer['last_heard']))
                htmlfile.write('</tr>\n')

                all_talk_groups = list(peer['talk_groups'].values())
                sorted_talk_groups = sorted(all_talk_groups, key=lambda tg: tg['total_elapsed'], reverse=True)
                # sorted_talk_groups = sorted(all_talk_groups, key=lambda tg: tg['talk_group_number'])
                for talk_group in sorted_talk_groups:
                    htmlfile.write('<tr class="tg-row">')
                    if talk_group['talk_group_number'] < 1:
                        bad_talk_group_number = talk_group['talk_group'].split(' ')[-1]
                        htmlfile.write('<td class="tg-col-1 unknown-tg" colspan="2">{:18s}</td>'.format(talk_group['talk_group']))
                        htmlfile.write('<td class="unknown-tg right">{}</td>'.format(bad_talk_group_number))
                    else:
                        htmlfile.write('<td class="tg-col-1" colspan="2">{:s}</td>'.format(talk_group['talk_group']))
                        htmlfile.write('<td class="right">{:d}</td>'.format(talk_group['talk_group_number']))
                    htmlfile.write('<td class="right">{:d}</td>'.format(talk_group['count']))
                    htmlfile.write('<td>{:s}'.format(convert_elapsed(talk_group['total_elapsed'])))
                    htmlfile.write('<td>{:%Y-%m-%d %H:%M}</td>'.format(talk_group['last_heard']))
                    htmlfile.write('</tr>\n')

        htmlfile.write('</table>\n')
        htmlfile.write('</div>\n')
        htmlfile.write('<p class="subhead">\n')
        htmlfile.write('<b>A note about "Unknown Ipsc Groups"</b><br>\n')
        htmlfile.write('There are several likely reasons you may see "Unknown Ipsc Group":\n')
        htmlfile.write('</p>\n')
        htmlfile.write('<div class="centered">')
        htmlfile.write('<ul>\n')
        htmlfile.write('<li>Use of a Brandmeister talk group number on a C-Bridge repeater.\n')
        htmlfile.write('<li>The talk group number is correct, but the timeslot is not.\n')
        htmlfile.write('<li>The talk group number is incorrect.\n')
        htmlfile.write('</ul>\n')
        htmlfile.write('</div>\n')
        htmlfile.write('</body></html>\n')


def print_users_detail(users_list):
    print("%d users sorted by time usage" % len(users_list))
    print('Call    Name               Contact ID  Count     Time      Last Heard UTC ')
    print('------  ------------------ ----------  ----- ----------   ----------------')
    for user in users_list:
        print('{:<6s}  {:<18s} {:10d}  {:5d} {:>10s}   {:%Y-%m-%d %H:%M}'.format(user['radio_name'],
                                                                                 user['radio_username'],
                                                                                 user['radio_id'],
                                                                                 user['count'],
                                                                                 convert_elapsed(user['total_elapsed']),
                                                                                 user['last_heard']))
        user_peers = user['peers'] or {}
        all_peers = list(user_peers.values())
        sorted_peers = sorted(all_peers, key=lambda peer: peer['total_elapsed'], reverse=True)
        for peer in sorted_peers:
            print('  {:<20s}     {:10d}  {:>5d} {:>10s}   {:%Y-%m-%d %H:%M}'
                  .format(peer['peer_callsign'],
                          peer['peer_id'],
                          peer['count'],
                          convert_elapsed(peer['total_elapsed']),
                          peer['last_heard']))
            # print(peer)
            all_talk_groups = list(peer['talk_groups'].values())
            sorted_talk_groups = sorted(all_talk_groups, key=lambda tg: tg['total_elapsed'], reverse=True)
            # sorted_talk_groups = sorted(all_talk_groups, key=lambda tg: tg['talk_group_number'])
            for talk_group in sorted_talk_groups:
                print('    {:<24s} {:8d}  {:5d} {:>10s}   {:%Y-%m-%d %H:%M}'
                      .format(talk_group['talk_group'],
                              talk_group['talk_group_number'],
                              talk_group['count'],
                              convert_elapsed(talk_group['total_elapsed']),
                              talk_group['last_heard']))
        # print()


def write_users_summary_html(users_list, heading='', filename='users_summary.html'):
    header_lines = read_file('log_analytics_fragment.html')
    with open(filename, 'w') as htmlfile:
        htmlfile.write('<html lang="i-klingon">\n<head>\n')
        htmlfile.write('<title>' + heading + '</title>\n')
        if header_lines is not None:
            htmlfile.writelines(header_lines)
        htmlfile.write("""
  <meta name="viewport" content="width=device-width, initial-scale=0.75">    
  <style>
BODY {
    margin: 0;
    border: 0;
    font-family: sans-serif;
}
.users-table {
    border-collapse: collapse;
    font-size: 0.8em;
    margin-left: auto;
    margin-right: auto;
}
.user-row-0 {
    background-color: #cfc;
}
.user-row-1 {
    background-color: #cff;
}
.header-row {
    background-color: #ccc;
}
TABLE, TH, TD {
    border: solid black 1px;
    padding: 2px
}
.right {
    text-align:right;
}
.heading {
    text-align:center;
    font-size: 1.5em;
    font-weight: bold;
}
.subhead {
    text-align:center;
    font-size: 0.85em;
}
  </style>
</head>
""")
        htmlfile.write('<body>\n')
        htmlfile.write('<p class="heading">' + heading + '</p>\n')
        htmlfile.write('<p class="subhead">\n')
        htmlfile.write('Sorted by callsign, useful for manual edit in CPS<br>\n')
        htmlfile.write('Users with low usage (count < 5, elapsed time < 10 seconds) are not shown on this report.\n')
        htmlfile.write('</p>\n')
        htmlfile.write('<div>\n')
        htmlfile.write('<table class="users-table">\n')
        htmlfile.write('<tr class="header-row"><th>Call</th><th>Name</th><th>Contact ID</th><th>Count</th><th>Elapsed</th><th>Last Heard UTC</th></tr>\n')
        count = 0
        for user in users_list:
            count += 1
            odd = count % 2
            htmlfile.write('<tr class="user-row-' + str(odd) + '">')
            htmlfile.write('<td>{:s}</td>'.format(user['radio_name']))
            htmlfile.write('<td>{:s}</td>'.format(user['radio_username']))
            htmlfile.write('<td class="right">{:d}</td>'.format(user['radio_id']))
            htmlfile.write('<td class="right">{:d}</td>'.format(user['count']))
            htmlfile.write('<td>{:s}'.format(convert_elapsed(user['total_elapsed'])))
            htmlfile.write('<td>{:%Y-%m-%d %H:%M}</td>'.format(user['last_heard']))
            htmlfile.write('</tr>\n')
        htmlfile.write('</table>\n')
        htmlfile.write('</div>\n')
        htmlfile.write('</body></html>\n')


def print_users_summary(users_list):
    print("%d top users, sorted by callsign" % len(users_list))
    print('Callsign  Name              Radio ID  Count    Time  ')
    print('--------  ----------------  --------  -----  --------')
    for user in users_list:
        print('{:<8s}  {:<16s}  {:>8d}  {:>5d}  {:8s}'.format(user['radio_name'],
                                                              user['radio_username'],
                                                              user['radio_id'],
                                                              user['count'],
                                                              convert_elapsed(user['total_elapsed'])))


def normalize_talkgroup_names(calls):
    for call in calls:
        site = call.get('site')
        call['dest'] = filter_talk_group_name(call.get('dest') or '!missing!')
        network = site_name_to_network_map.get(site)
        tgid = call.get('tgid') or '0'
        found_tg_name = False

        if network is not None:
            if network == 'Brandmeister':
                tgid_int = safe_int(tgid)
                if tgid_int != 0:
                    tg_data = talk_group_number_to_data_mapping[network].get(tgid_int)
                    if tg_data is not None:
                        new_dest = tg_data.get('description')
                        if new_dest is not None:
                            current_dest = call.get('dest')
                            if current_dest != new_dest:
                                logging.debug(f'replacing dest {current_dest} with {new_dest}')
                                call['dest'] = new_dest
                            found_tg_name = True
                    else:
                        if tgid_int > 999999:
                            found_tg_name = True  # not found, not gonna find.
                        else:
                            # logging.warning(f'no tgdata for {network} {tgid_int}')
                            call['dest'] = f'Unknown Talkgroup {tgid_int}'
                            found_tg_name = True  # not found, not gonna find.
                else:  # tg_id is 0
                    #logging.info(f'Brandmeister with tg_id=0 {call}')
                    found_tg_name = True
            else:
                dest = call.get('dest') or '!missing!'
                if dest.startswith('Unknown Ipsc group '):
                    tg_str = dest[19:]
                    call['tgid'] = tg_str
                    found_tg_name = True  # found it to have no name.
                else:
                    tg_data = talk_group_name_to_number_mapping[network].get(dest)
                    if tg_data is not None:
                        call['tgid'] = str(tg_data.get('tg') or 0)
                        call['dest'] = tg_data.get('description')
                        found_tg_name = True
                    else:
                        logging.warning(f'No talk group data for {network} {dest}')
                        found_tg_name = True
        else:
            logging.error('network is none! {call}')

        if not found_tg_name:
            logging.warning(f'could not find talkgroup name for {call}')


def main():
    now = datetime.datetime.now(datetime.timezone.utc)
    # start_time = now - datetime.timedelta(days=365)
    end_time = now
    if len(sys.argv) >= 2:
        if sys.argv[1].lower() == '--all':
            logging.info('selected all data.')
            start_time = datetime.datetime.strptime('2019-12-01 00:00:00+00:00', '%Y-%m-%d %H:%M:%S%z')
        elif sys.argv[1].lower() == '--year':
            logging.info('selected the last year\'s data.')
            start_time = now - datetime.timedelta(days=365)
    else:
        logging.info('last 30 days mode.')
        start_time = now - datetime.timedelta(days=30)

    # start_time = datetime.datetime.strptime('2020-02-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    # start_time = datetime.datetime.strptime('2020-03-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    # start_time = datetime.datetime.strptime('2020-04-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    # end_time = datetime.datetime.strptime('2020-01-31 23:59:59', '%Y-%m-%d %H:%M:%S')
    # end_time = datetime.datetime.strptime('2020-02-29 23:59:59', '%Y-%m-%d %H:%M:%S')

    emit_repeaters = False
    if emit_repeaters:
        repeaters = []
        for repeater in repeaters:
            talkgroups = repeater.get('talk_groups')
            talk_groups = []
            for talkgroup in talkgroups:
                talk_groups.append({'number': talkgroup[0],
                                    'slot': talkgroup[1],
                                    'static': talkgroup[2]
                                    })
            repeater['talk_groups'] = talk_groups

        with open('repeaters.json', 'w') as data_file:
            json.dump(repeaters, data_file, indent=2)

        sys.exit(0)

    with open('repeaters.json', 'rb') as repeaters_data_file:
        repeaters = json.load(repeaters_data_file)

    logging.info(f'loaded {len(repeaters)} repeaters from file.')

    calls_data_file = 'async_logged_calls.txt'
    calls = read_log(calls_data_file, start_time, end_time)

    calls = sorted(calls, key=lambda call: call.get('timestamp'))

    normalize_talkgroup_names(calls)

    if len(calls) > 0:
        first_date = calls[0]['timestamp']
        logging.info('first record: {}'.format(first_date))

        if first_date > start_time:
            start_time = datetime.datetime(year=first_date.year,
                                           month=first_date.month,
                                           day=first_date.day,
                                           tzinfo=first_date.tzinfo)
            logging.info('resetting start_time to {}'.format(start_time))

        logging.info(' last record: {}'.format(calls[-1]['timestamp']))
        date_header = 'From {} to {}'.format(calls[0]['timestamp'], calls[-1]['timestamp'])

        talk_groups = {}
        users = {}
        peers = {}

        timeseries = {}
        chart_talk_groups = {}

        # crunch data, assume it is clean
        num_days = (end_time - start_time).days
        if num_days <= 14:
            bin_hours = 1
            bins_start = start_time.replace(minute=0, second=0, microsecond=0)
            bins_end = end_time.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
        elif num_days <= 30:
            bin_hours = 3
            bins_start = start_time.replace(minute=0, second=0, microsecond=0)
            h = bins_start.hour // bin_hours * bin_hours  # bin into 24 / bin_hours bins
            bins_start = bins_start.replace(hour=h)
            bins_end = end_time.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
            bins_end = bins_end.replace(hour=h)
        else:
            bin_hours = 24
            bins_start = start_time.date()
            bins_end = end_time.date() + datetime.timedelta(days=1)

        this_bin_key = bins_start
        while this_bin_key <= bins_end:
            timeseries[this_bin_key] = {'date': this_bin_key}
            this_bin_key = this_bin_key + datetime.timedelta(hours=bin_hours)

        for call in calls:
            ts = call.get('timestamp')
            if type(ts) != datetime.datetime:
                print(type(ts))
                print('wtf')
                print(call)
                continue
            if num_days <= 7:
                dt = ts.replace(minute=0, second=0, microsecond=0)  # bin into hours
            elif num_days <= 30:
                dt = ts.replace(minute=0, second=0, microsecond=0)
                h = ts.hour // bin_hours * bin_hours  # bin into 24 / bin_hours bins
                dt = dt.replace(hour=h)
            else:
                dt = ts.date()  # this forces bins into days

            radio_id = call.get('radio_id') or 0
            radio_name = call.get('radio_name')
            radio_username = call.get('radio_username')
            talk_group_name = call.get('dest') or 'unknown'
            peer_id = call.get('peer_id') or 0
            try:
                duration = float(call.get('duration')) or 0.0
            except Exception as e:
                print(e)
                print(call)
            # build/add to timeseries
            this_bin = timeseries.get(dt)
            if this_bin is None:
                this_bin = {'date': dt}
                timeseries[dt] = this_bin
            # if talk_group_name in interesting_talk_group_names:
            if True:
                this_bin_tg = this_bin.get(talk_group_name)
                if this_bin_tg is None:
                    this_bin_tg = {'count': 0, 'duration': 0.0}
                    this_bin[talk_group_name] = this_bin_tg
                this_bin_tg['count'] += 1
                this_bin_tg['duration'] += duration
                chart_talk_group = chart_talk_groups.get(talk_group_name)
                if chart_talk_group is None:
                    chart_talk_groups[talk_group_name] = {'talk_group': talk_group_name, 'duration': 0.0}

                chart_talk_groups[talk_group_name]['duration'] += duration
                # if duration > chart_talk_groups[talk_group_name]['duration']:
                #    chart_talk_groups[talk_group_name]['duration'] = duration

            if radio_id < 1000000:
                # print('unknown radio id {}'.format(rid))
                continue
            if radio_name == 'N/A':
                continue

            user = users.get(radio_id)
            if user is None:
                user = {'radio_id': radio_id,
                        'radio_name': radio_name,
                        'radio_username': radio_username,
                        'count': 0,
                        'total_elapsed': 0,
                        'peers': {},
                        'talk_groups': {},
                        'last_heard': None}
                users[radio_id] = user
            else:
                if user['radio_name'] == 'N/A':
                    user['radio_name'] = radio_name
                if user['radio_username'] == 'N/A':
                    user['radio_username'] = radio_username
            update_usage(user, call)
            update_peer(user['peers'], call)

            #  if peer_id in interesting_peer_ids:
            if True:
                update_peer(peers, call)

            if not talk_group_name.lower().startswith('unknown'):
                talk_group = talk_groups.get(talk_group_name)
                if talk_group is None:
                    talk_group = {'talk_group': talk_group_name,
                                  'count': 0,
                                  'total_elapsed': 0,
                                  'last_heard': None
                                  }
                    talk_groups[talk_group_name] = talk_group
                talk_group['count'] += 1
                talk_group['total_elapsed'] += duration
                talk_group['last_heard'] = None

        all_talkgroups = list(talk_groups.values())
        sorted_talkgroups = sorted(all_talkgroups, key=lambda tg: tg['total_elapsed'], reverse=True)
        # print()
        # print_talkgroups(sorted_talkgroups)
        # print()

        all_peers = []
        for peer_id in peers:
            peer = peers[peer_id]
            if peer['count']: #  > 2: #  and peer['total_elapsed'] > 5:
                all_peers.append(peer)

        all_peers = sorted(all_peers, key=lambda peer: peer['total_elapsed'], reverse=True)

        # print()
        # print_peers(all_peers)
        # print()

        all_users = []
        # narrow users into all_users.
        min_count = 5
        min_time = 10
        # min_mean_duration = 1
        discounted_users = 0
        for userkey in users:
            user = users[userkey]
            if user['count'] >= min_count and user['total_elapsed'] >= min_time:
                all_users.append(user)
            else:
                discounted_users += 1
        logging.info('(ignored {} users due to low count or low time.)'.format(discounted_users))

        all_users = sorted(all_users, key=lambda user: user['total_elapsed'], reverse=True)

        write_users_html(all_users, heading='Usage ' + date_header)

        # print_users_detail(all_users)
        # print()
        top_users = all_users[0:200]
        # top_users = all_users
        top_users = sorted(top_users, key=lambda user: user['radio_name'])

        # print_users_summary(top_users)

        write_users_summary_html(top_users, heading='Top Users ' + date_header)

        contact_list = sorted(all_users, key=lambda user: user['radio_id'])
        write_csv_contacts(contact_list)
        write_csv_moto_contacts(contact_list)
        write_peers_html(all_peers, heading='Peer Usage ' + date_header)

        validate_repeater_data(repeaters, all_peers)

        results = []
        for key in sorted(timeseries.keys()):
            # if key >= start_date and key <= end_date:
            results.append(timeseries[key])

        chart_date_header = 'From {} to {}'.format(results[0]['date'], results[-1]['date'])
        # charts.plot_activity(results, 'Talkgroup Activity ' + chart_date_header, filename='activity.png')
        charts.plot_activity_stackbar(results, 'Talkgroup Activity ' + chart_date_header, filename='activity.png')

    write_repeater_html(repeaters)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)
    logging.Formatter.converter = time.gmtime
    main()
