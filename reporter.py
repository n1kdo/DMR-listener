#!/bin/python36
import csv
import datetime

from common import interesting_talk_group_names, talk_group_name_to_number_mapping, talk_group_number_to_data_mapping
from common import repeaters
from common import interesting_peer_ids
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


def Zconvert_timestamp(s):
    try:
        t = datetime.datetime.strptime(s[0:8] + s[12:], "%H:%M:%S %b %d").replace(year=2019)
    except ValueError:
        t = None
    return t


def convert_iso_timestamp(s):
    try:
        return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None


def safe_int(s):
    try:
        return int(s)
    except ValueError:
        return -1


def read_log(filename, start, end):
    calls = []
    fields = ['timestamp', 'site', 'dest', 'peer_id', 'peer_callsign', 'peer_name',
              'radio_id', 'radio_name', 'radio_username', 'duration']

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
                if ts < start or ts > end:
                    continue

            duration = row.get('duration') or '0'
            if duration is not None:
                row['duration'] = float(duration)
            else:
                row['duration'] = 0.0
            if row.get('peer_id') is not None:
                row['peer_id'] = safe_int(row['peer_id'])
            if row.get('radio_id') is not None:
                row['radio_id'] = safe_int(row['radio_id'])
            if row.get('dest') is not None:
                talk_group = filter_talk_group_name(row['dest'])
                peer_id = row.get('peer_id')
                # filter out talk groups that are uninteresting
                if talk_group not in interesting_talk_group_names and peer_id not in interesting_peer_ids:
                    continue
                row['talk_group'] = talk_group
            calls.append(row)

    print("read        %6d rows" % rows)
    print("filtered to %6d records" % len(calls))
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


def write_repeater_html():
    """
    write data for web
    :return:
    """
    filename = 'repeaters.html'
    with open(filename, 'w') as htmlfile:
        htmlfile.write('<html>\n')
        htmlfile.write("""
<style>
BODY {
    margin: 0;
    border: 0;
    font-family: sans-serif;
}
.notes {
    font-size: 1em;
    text-align: center;
}
.repeater-header {
    background-color: #cff;
    font-size: 2em;
    font-weight: bold;
    margin-block-end: 0;
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
    Zborder-radius: 8px;
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
    background-color: #ccc;
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
</style>
""")
        htmlfile.write('<body>\n')
        htmlfile.write('<div class="heading">Metro Atlanta Area DMR Repeaters</div>')
        htmlfile.write('<div class="tabs">')
        ctr = 1
        for repeater in repeaters:
            htmlfile.write('<div class="tab">')
            htmlfile.write('<input type="checkbox" id="chck{}">'.format(ctr))
            rptr = '{} {} {} Color Code {}, {} network'.format(repeater['call'], repeater['output'], repeater['location'], repeater['color_code'], repeater['network'])
            htmlfile.write('<label class="tab-label" for="chck{}">{}</label>'.format(ctr, rptr))
            htmlfile.write('<div class="tab-content">')
            htmlfile.write('<table class="talk-groups-table" border="1">\n')
            talk_groups = repeater['talk_groups']
            htmlfile.write('<tr><th>Talk Group<br>Name</th><th>Talk<br>Group<br>#</th><th>Time<br>Slot<br>#</th><th>Notes</th></tr>\n')
            for ts in [1, 2]:
                for talk_group in talk_groups:
                    tg_number = talk_group[0]
                    tg_timeslot = talk_group[1]
                    tg_mode = talk_group[2]
                    talk_group_data = talk_group_number_to_data_mapping[repeater['network']].get(tg_number)
                    if talk_group_data is None:
                        print('missing talk group data for tg {}'.format(tg_number))
                        break
                    if tg_timeslot == ts:
                        if tg_mode == 0:
                            notes = 'static'
                        else:
                            notes = ''
                        htmlfile.write('<tr><td class="tg-name">{}</td><td class="tg-number">{}</td><td class="tg-number">{}</td><td class="tg-number">{}</td></tr>\n'.format(talk_group_data['description'], tg_number, tg_timeslot, notes))
            htmlfile.write('</table>\n')
            notes = repeater.get('notes')
            if notes is not None:
                htmlfile.write('<p class="notes">{}</p>'.format(notes))
            htmlfile.write('</div>')
            htmlfile.write('</div>')
            ctr += 1
        htmlfile.write('</div>')
        htmlfile.write('</body></html>\n')


def validate_repeater_data(repeaters_list, peers_list):
    print('\nvaliding talkgroup lists...\n')
    for peer in peers_list:
        peer_id = peer['peer_id']
        repeater_found = False
        for repeater in repeaters_list:
            if int(repeater['peer_id']) == peer_id:
                repeater_talk_groups = repeater['talk_groups']
                peer_talk_groups = peer['talk_groups']
                for peer_talk_group in peer_talk_groups:
                    ptgn = peer_talk_groups[peer_talk_group]['talk_group_number']
                    if ptgn == -1:
                        continue
                    talk_group_found = False
                    for repeater_talk_group in repeater_talk_groups:
                        rtgn = repeater_talk_group[0]
                        if ptgn == rtgn:
                            talk_group_found = True
                    if not talk_group_found:
                        print('did not find matching tg {} on repeater {}'.format(ptgn, peer_id))
                repeater_found = True
        if not repeater_found:
            print('Could not find a repeater matching peer_id {}'.format(peer_id))


def update_usage(a_dict, call):
    talk_group_name = call.get('talk_group')
    timestamp = call['timestamp']
    duration = call.get('duration') or 0.0
    usage_dict = a_dict['talk_groups'].get(talk_group_name)
    if usage_dict is None:
        talk_group_data = talk_group_name_to_number_mapping['K4USD'].get(talk_group_name)
        if talk_group_data is None:
            talk_group_number = -1
        else:
            talk_group_number = talk_group_data['tg']
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
    if peer_name == 'n/a':
        peer_name = '{}'.format(peer_id)
    if peer_callsign == 'n/a':
        if peer_name != 'n/a':
            peer_callsign = peer_name
        else:
            peer_callsign = 'unknown peer'
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
    print('   Peer ID Callsign             Peer Name                      Count    Elapsed    Last Heard UTC ')
    print('---------- -------------------- ------------------------------ ----- ----------   ----------------')
    for peer in peers_list:
        print('{:10d} {:<20s} {:<30s} {:5d} {:>10s}   {:%Y-%m-%d %H:%M}'
              .format(peer['peer_id'], peer['peer_callsign'], peer['peer_name'],
                      peer['count'], convert_elapsed(peer['total_elapsed']), peer['last_heard']))
        peer_talk_groups = peer['talk_groups']
        all_talk_groups = list(peer_talk_groups.values())
        # sorted_talk_groups = sorted(all_talk_groups, key=lambda tg: tg['total_elapsed'], reverse=True)
        sorted_talk_groups = sorted(all_talk_groups, key=lambda tg: tg['talk_group_number'])
        for talk_group in sorted_talk_groups:
            if talk_group['talk_group'].startswith('UnKnown'):
                continue
            print('                                * {:6d} {:<20s}  {:5d} {:>10s}   {:%Y-%m-%d %H:%M}'
                  .format(talk_group['talk_group_number'],
                          talk_group['talk_group'],
                          talk_group['count'],
                          convert_elapsed(talk_group['total_elapsed']),
                          talk_group['last_heard']))


def print_talkgroups(talkgroups_list):
    print('----- talkgroups  heard -----')
    print('tg name        TG # count   elapsed ')
    print('------------ ------ ----- ----------')
    for tg in talkgroups_list:
        talk_group_data = talk_group_name_to_number_mapping['K4USD'].get(tg['talk_group'])
        if talk_group_data is None:
            talk_group_number = -1
        else:
            talk_group_number = talk_group_data['tg']
        print('%-12s %6d %5d %10s' % (tg['talk_group'],
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


def main():
    now = datetime.datetime.utcnow()
    #start_time = now - datetime.timedelta(days=365)
    start_time = now - datetime.timedelta(days=90)
    end_time = now
    #start_time = datetime.datetime.strptime('2019-12-07 00:00:00', '%Y-%m-%d %H:%M:%S') #  first date in current file
    # start_time = datetime.datetime.strptime('2020-02-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    # start_time = datetime.datetime.strptime('2020-03-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    start_time = datetime.datetime.strptime('2020-04-01 00:00:00', '%Y-%m-%d %H:%M:%S')
    # end_time = datetime.datetime.strptime('2020-01-31 23:59:59', '%Y-%m-%d %H:%M:%S')
    # end_time = datetime.datetime.strptime('2020-02-29 23:59:59', '%Y-%m-%d %H:%M:%S')

    calls = read_log('logged_calls.txt', start_time, end_time)
    # show a sample row of data
    print('first record: {}'.format(calls[0]['timestamp']))
    print(' last record: {}'.format(calls[-1]['timestamp']))

    talk_groups = {}
    users = {}
    peers = {}

    timeseries = {}

    # crunch data, assume it is clean
    for call in calls:
        ts = call.get("timestamp")
        dt = ts.date()  # this forces bins into days
        # dt = ts.replace(minute=0, second=0, microsecond=0)  # bin into hours
        radio_id = call.get('radio_id') or 0
        radio_name = call.get('radio_name')
        radio_username = call.get('radio_username')
        talk_group_name = call.get('talk_group') or 'unknown'
        peer_id = call.get('peer_id') or 0
        duration = call.get('duration') or 0.0
        # build/add to timeseries
        this_day = timeseries.get(dt)
        if this_day is None:
            this_day = {'date': dt}
            timeseries[dt] = this_day
        if talk_group_name in interesting_talk_group_names:
            this_day_tg = this_day.get(talk_group_name)
            if this_day_tg is None:
                this_day_tg = {'count': 0, 'duration': 0.0}
                this_day[talk_group_name] = this_day_tg
            this_day_tg['count'] += 1
            this_day_tg['duration'] += duration

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

        if peer_id in interesting_peer_ids:
            update_peer(peers, call)

        if not talk_group_name[0:7] == 'UnKnown':
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
    print()
    print_talkgroups(sorted_talkgroups)
    print()

    all_peers = []
    for peer_id in peers:
        peer = peers[peer_id]
        if peer['count'] > 2 and peer['total_elapsed'] > 5:
            all_peers.append(peer)

    all_peers = sorted(all_peers, key=lambda peer: peer['total_elapsed'], reverse=True)

    print()
    print_peers(all_peers)
    print()

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
    print('(ignored {} users due to low count or low time.)'.format(discounted_users))

    all_users = sorted(all_users, key=lambda user: user['total_elapsed'], reverse=True)
    print_users_detail(all_users)
    print()
    top_users = all_users[0:200]
    # top_users = all_users
    top_users = sorted(top_users, key=lambda user: user['radio_name'])

    print_users_summary(top_users)

    contact_list = sorted(all_users, key=lambda user: user['radio_id'])
    write_csv_contacts(contact_list)
    write_csv_moto_contacts(contact_list)
    write_repeater_html()

    validate_repeater_data(repeaters, all_peers)

    results = []
    for key in sorted(timeseries.keys()):
        # if key >= start_date and key <= end_date:
        results.append(timeseries[key])

    charts.plot_activity(results, interesting_talk_group_names[:2], 'Talkgroup Activity', filename='activity.png')


if __name__ == '__main__':
    main()
