#!/usr/bin/env python3

import json
import logging
import requests
import time


def safe_int(s):
    if isinstance(s, int):
        return s
    try:
        return int(s)
    except ValueError:
        return -1


def query_brandmeister_talkgroups(repeater_id):
    r = requests.get(f'https://api.brandmeister.network/v2/device/{repeater_id}/talkgroup')
    data = r.json()
    talk_groups = []
    for talk_group in data:
        talk_group.pop('repeaterid')
        talk_group['talkgroup'] = safe_int(talk_group.pop('talkgroup') or 0)
        talk_group['slot'] = safe_int(talk_group.pop('slot') or 0)
        talk_group['mode'] = 0  # 0 is static
    return data


def main():
    with open('repeaters.json', 'rb') as repeaters_data_file:
        repeaters = json.load(repeaters_data_file)

    updated = 0
    logging.info(f'loaded {len(repeaters)} repeaters from file.')

    for repeater in repeaters:
        network = repeater.get('network') or ''
        if network == 'Brandmeister':
            peer_id = repeater.get('peer_id') or -1
            new_talk_groups = query_brandmeister_talkgroups(peer_id)
            if len(new_talk_groups) > 0:
                new_len = len(new_talk_groups)
                old_len = len(repeater.get('talk_groups'))
                old_len = 0  # DEBUG
                if new_len != old_len:
                    #print(peer_id)
                    #print(repeater.get('talk_groups'))
                    #print(new_talk_groups)
                    repeater['talk_groups'] = new_talk_groups
                    updated += 1
    if updated:
        logging.info(f'updated {updated} repeater static talk groups')
        with open('repeaters.json', 'w') as data_file:
            json.dump(repeaters, data_file, indent=2)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)
    logging.Formatter.converter = time.gmtime
    main()
