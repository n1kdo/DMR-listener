"""
script adds repeater to repeaters.json

"""
import json
import logging
import requests
import time

import common


def safe_int(s):
    if isinstance(s, int):
        return s
    try:
        return int(s)
    except ValueError:
        return -1


def query_radioid_net(repeater_id):
    r = requests.get(f'https://radioid.net/api/dmr/repeater/?id={repeater_id}', verify=False)
    data = r.json()
    count = data.get('count') or 0
    if count == 1:
        data = data.get('results') or []
        if len(data) == 1:
            return data[0]
    return None


def get_talkgroup_data(data):
    talk_groups = []
    # print(data)
    details = data.get('details') or ''
    details = details.replace('<br>', '\n')
    print(details)
    rfinder_text = data.get('rfinder') or ''
    rfinder_text = rfinder_text.replace('<br>', '\n')
    print(rfinder_text)
    while True:
        line = input('enter TG ID, slot, mode or nothing to end: ')
        if len(line.strip()) == 0:
            break
        stuff = line.split(',')
        if len(stuff) != 3:
            print('try 3 values seperated by commas, please.')
            continue
        tg_id = safe_int(stuff[0].strip())
        slot = safe_int(stuff[1].strip())
        mode = safe_int(stuff[2].strip())
        if tg_id < 1 or tg_id > 9999999:
            print(f'talkgroup number {tg_id} is not valid.  Try again.')
            continue
        if slot not in [1, 2]:
            print(f'invalid slot {slot} -- must be 1 or 2. Try again.')
            continue
        talk_groups.append({'talkgroup': tg_id,
                            'slot': slot,
                            'mode': mode,
                            })

    return sorted(talk_groups, key=lambda x: x['slot'] * 1000000 + x['talkgroup'])


def query_brandmeister_talkgroups(repeater_id):
    r = requests.get(f'https://api.brandmeister.network/v2/device/{repeater_id}/talkgroup')
    data = r.json()
    for talk_group in data:
        talk_group.pop('repeaterid')
        talk_group['talkgroup'] = safe_int(talk_group.pop('talkgroup') or 0)
        talk_group['slot'] = safe_int(talk_group.pop('slot') or 0)
        talk_group['mode'] = 0  # 0 is static
    return sorted(data, key=lambda x: x['slot'] * 1000000 + x['talkgroup'])


def main():
    with open('repeaters.json', 'rb') as repeaters_data_file:
        repeaters = json.load(repeaters_data_file)
    logging.info(f'loaded {len(repeaters)} repeaters from file.')
    peers_list = sorted([safe_int(repeater.get('peer_id') or '') for repeater in repeaters])
    updated = 0

    while True:
        print('\n')
        peer_id = safe_int(input('ID for repeater to add? '))
        # peer_id = 310051
        if peer_id < 1:
            break

        if not 99999 < peer_id < 999999:
            print(f'invalid repeater id')
            continue

        if peer_id in peers_list:
            print(f'peer {peer_id} is already known.')
            continue

        # now fetch data from radioid.net
        repeater_data = query_radioid_net(peer_id)
        if repeater_data is None:
            print(f'WARNING: no data in radioid.net for {peer_id}')
            exit(0)
        location = repeater_data.get('city') + ', ' + repeater_data.get('state')
        tx = float(repeater_data.get('frequency') or 0)
        offset = float(repeater_data.get('offset') or 0)
        rx = round(tx + offset, 4)
        network = repeater_data.get('ipsc_network')
        if network in ['BM', 'BM3102']:  # try to prevent GIGO
            network = 'Brandmeister'
        if network.lower() == 'brandmeister':
            network = "Brandmeister"

        while network not in common.networks:
            print(f'Unknown Network {network}')
            network = input('Enter network name: ')

        talk_groups = []
        if network == 'Brandmeister':
            talk_groups = query_brandmeister_talkgroups(peer_id)
        else:
            print(f'Network = {network}')
        if len(talk_groups) == 0:
            talk_groups = get_talkgroup_data(repeater_data)

        if len(talk_groups) > 0:
            new_repeater = {
                'peer_id': peer_id,
                'call': (repeater_data.get('callsign') or '?').upper(),
                'input': f'{rx}',
                'output': f'{tx}',
                'color_code': str(repeater_data.get('color_code') or '?'),
                'location': location,
                'network': network,
                'talk_groups': talk_groups,
            }
            repeaters.append(new_repeater)
            peers_list.append(peer_id)
            updated += 1
        else:
            print(f'Not adding repeater {peer_id}, no talk groups.')

    if updated > 0:
        repeaters.sort(key=lambda repeater: repeater['call'])
        with open('repeaters.json', 'w') as data_file:
            json.dump(repeaters, data_file, indent=2)
    print(f'added {updated} repeaters')


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)
    logging.Formatter.converter = time.gmtime
    main()
