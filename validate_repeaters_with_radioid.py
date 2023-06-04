"""
script validates location, color code, and output frequency for repeaters in repeaters.json
"""
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


def query_radioid_net(repeater_id):
    r = requests.get(f'https://radioid.net/api/dmr/repeater/?id={repeater_id}')
    data = r.json()
    count = data.get('count') or 0
    if count == 1:
        data = data.get('results') or []
        if len(data) == 1:
            return data[0]
    return None


def get_talkgroup_data(data):
    print(data)
    details = data.get('details') or ''
    details = details.replace('<br>', '\n')
    print(details)
    rfinder_text = data.get('rfinder') or ''
    rfinder_text = rfinder_text.replace('<br>', '\n')
    print(rfinder_text)
    return []


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
        print(f'looking at #{repeater.get("peer_id")} {repeater.get("call")}')
        peer_id = safe_int(repeater.get('peer_id') or -1)
        if peer_id > 0:
            dirty = False
            repeater_data = query_radioid_net(peer_id)
            if repeater_data is None:
                print(f'WARNING: no data in radioid.net for {peer_id}')
                continue
            location = repeater_data.get('city') + ', ' + repeater_data.get('state')
            my_location = repeater.get('location')
            if my_location != location and location not in my_location:
                print(f'location mismatch! old location was {repeater.get("location")}, radioid has {location}.')
                repeater['location'] = location
                output = float(repeater.get('output') or 0)
                frequency = float(repeater_data.get('frequency') or 0)
                if output != frequency:
                    print(f'freq mismatch, mine: {output}, radioid:{frequency}')
                my_color_code = safe_int(repeater.get('color_code') or -1)
                color_code = safe_int(repeater_data.get('color_code') or -1)
                if my_color_code != color_code:
                    print(my_color_code, color_code)
            #rint(repeater)
            #rint(repeater_data)
            print('----------------------')
            # updated += 1
        # break
    if updated:
        logging.info(f'updated {updated} repeater static talk groups')
        with open('repeaters.json', 'w') as data_file:
            json.dump(repeaters, data_file, indent=2)


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.INFO)
    logging.Formatter.converter = time.gmtime
    main()
