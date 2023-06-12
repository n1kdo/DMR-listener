import logging
import json
import re

# all traffic to these talk groups will be logged.
interesting_talk_group_names = [
    'ATL Metro',
    'Atlanta Metro',
    #  'Bridge',
    'GAstate',
    'Georgia',
    'GA ARES',
    'Georgia ARES',
    'GA North',
    'North Georgia',
    'GA Skywarn',
    'Georgia Skywarn'
    "SEreg",
    #"Vdalia Net",
    #"Vidalia Net",
]

interesting_talk_groups = [3113, 31130, 31131, 31132, 31133, 31134, 31135, 31136, 31137, 31138, 31139, 311340, 3113090, ]

less_interesting_talk_group_names = [  # for debugging with more volume
    'TAC 310',
    'TAC 311',
    'TAC 312',
    'TAC 313',
    'TAC 314',
    'TAC 315',
    'TAC 316',
    'TAC 317',
    'TAC 318',
    'TAC 319',
    'BM USA Bridge',
    'BM Worldwide',
]

less_interesting_talk_groups = [91, 93, 310, 311, 312, 313, 314, 315, 315, 317, 318, 319, 3100, ]

# all traffic from the interesting peers will be logged.  Best to not turn on brandmeister.
interesting_peers = {
    310051: 'K5TEX Free Home',
    310293: 'W4BOC Stone Mountain',
    310295: "W4KIP Little Sweat Mountain",
    310371: 'W4DOC Atlanta',
    310466: 'K4VYX Savannah',
    310592: 'KG4BKO Vidalia',
    310969: 'W4KST Marietta',
    310996: 'KM4EYX Douglas',
    311303: 'KE4OKD Sandy Springs',
    311304: 'N8WHG Jasper',
    311307: 'W1KFR Kingsland',
    311308: 'K4VLD Valdosta',
    311314: 'KD4KHO Canton',
    311315: 'N8WHG Powder Springs',
    311318: 'K4KHR Kingsland',
    311319: 'KD4GGY Jesup',
    311320: 'W4CBA Cumming',
    311321: 'N4TAW  Between',
    311322: 'KA3JIJ Gainesville',
    311325: 'N4IRR Marietta',
    311326: 'AI1U Lawrenceville',
    311329: 'KE4UAS McDonough',
    311334: 'K4KV Tifton',
    311336: 'AI1U Lawrenceville',
    311337: 'WA4ASI Covington',
    311338: 'KD4Z Roswell',
    311339: 'KD4APP Ball Ground',
    311340: 'W4KIP Marietta',
    311343: 'W4KIP Marietta',
    311344: 'W4KIP Atlanta',
    311347: 'WB4BXO LaGrange',
    311348: 'WR4SG Valdosta',
    311350: 'KM4DND Waycross',
    311428: 'N4MPC Decatur',
    311563: 'WA4ASI Covington',
    311617: 'KE4PMP Parrot GA',
    311637: 'NG4RF Cumming',
    311639: 'K4EGA Eatonton',
    312243: 'N4RMG Rome',
    312284: 'KD4IEZ Dublin',
    312288: 'AF1G Kathleen',
    312384: 'KZ4FOX Athens',
    312391: 'KE4PMP Cochrane',
    312429: 'KE4RJI Tifton',
    312444: 'KZ4FOX Athens',
    312477: 'WX4EMA Macon',
    312779: 'WY4EMY Kathleen',
    313132: 'W4BOC Stone Mountain',
    313269: 'AI1U Snellville',
    }

interesting_peer_ids = interesting_peers.keys()


# remap talk groups names on particular peers to make them consistent.  This helps to reduce GIGO.
remap_map = {
    -1: [{'tg_name_old': 'Vdalia Net', 'tg_name_new': 'Vidalia Net'}],
    0: [{'tg_name_old': 'Vdalia Net', 'tg_name_new': 'Vidalia Net'}],  # 0 will always remap.
    -3102: [{'tg_name_old': 'Vdalia Net', 'tg_name_new': 'Vidalia Net'}],
    310592: [{'tg_name_old': 'Vdalia Net', 'tg_name_new': 'Vidalia Net'}],
    310996: [{'tg_name_old': 'Vdalia Net', 'tg_name_new': 'Vidalia Net'}],
    312391: [{'tg_name_old': 'Vdalia Net', 'tg_name_new': 'Vidalia Net'}],
    312444: [{'tg_name_old': 'Local8', 'tg_name_new': 'ATL Metro'}],
    311307: [{'tg_name_old': 'Vdalia Net', 'tg_name_new': 'Vidalia Net'}],
    311318: [{'tg_name_old': 'Vdalia Net', 'tg_name_new': 'Vidalia Net'}],
    311350: [{'tg_name_old': 'Vdalia Net', 'tg_name_new': 'Vidalia Net'}],
    311617: [{'tg_name_old': 'Vdalia Net', 'tg_name_new': 'Vidalia Net'}],
    311637: [{'tg_name_old': 'Local8', 'tg_name_new': 'ATL Metro'}],
    312284: [{'tg_name_old': 'Vdalia Net', 'tg_name_new': 'Vidalia Net'}],
    312485: [{'tg_name_old': 'Vdalia Net', 'tg_name_new': 'Vidalia Net'}],
}


def filter_talk_group_name(tg_name):
    # Strip "CC" and everything after it.
    s = re.sub(r' CC.*', '', tg_name)
    # strip "CC" alone
    s = re.sub(r' CC', '', s)
    # strip out number-number-number
    s = re.sub(r' \d+-\d+-\d+', '', s)
    # strip out number-number
    s = re.sub(r' \d+-\d+', '', s)
    # print("%s | %s" % (s, old_s))
    # remove trailing TG <number>
    i = s.find(' TG ')
    if i > 0:
        s = s[0:i]
    s = s.strip()
    if len(s) < 1:
        logging.warning('talkgroup name filter problem: {} -> {}'.format(tg_name, s))
    return s


networks = ['Brandmeister', 'DMR-MARC', 'DMR-SE', 'K4USD', 'Ham Digital']

site_name_to_network_map = {
    'Brandmeister': 'Brandmeister',
    'BM-US-3102': 'Brandmeister',
    'DMR-MARC-CCEAST': 'DMR-MARC',
    'DMR-MARC-CCWEST': 'DMR-MARC',
    'DMR-SE': 'DMR-SE',
    'K4USD Network': 'K4USD',
    'K4USD-2 Network': 'K4USD',
    'Ham Digital': 'Ham Digital',
    'Homebrew Repeater': 'Brandmeister',  # obsolete
    'MMDVM Host': 'Brandmeister',  # obsolete
    'Motorola IP Site Connect': 'Brandmeister',  # obsolete
    }

""" 
mapping of C-bridge talkgroup name to talkgroup number to description
"""
talk_groups = {}

talk_groups['Brandmeister'] = [
    {'name': 'Local2', 'tg': 2, 'description': 'Local 2', },
    {'name': '2', 'tg': 2, 'description': 'Local 2', },
    {'name': 'Cluster', 'tg': 2, 'description': 'Local 2', },
    {'name': 'Local8', 'tg': 8, 'description': 'Local 8', },
    {'name': 'Regional', 'tg': 8, 'description': 'Local 8', },
    {'name': 'Local', 'tg': 9, 'description': 'Local 9', },
    {'name': 'World-wide', 'tg': 91, 'description': 'BM Worldwide', },
    {'name': 'North America', 'tg': 93, 'description': 'BM North America', },
    {'name': 'TAC310', 'tg': 310, 'description': 'TAC310', },
    {'name': 'Tac 310 NOT A CALL CHANNEL', 'tg': 310, 'description': 'TAC310', },
    {'name': 'TAC311', 'tg': 311, 'description': 'TAC311', },
    {'name': 'TAC 311 USA NO NETS!!!', 'tg': 311, 'description': 'TAC311', },
    {'name': 'TAC312', 'tg': 312, 'description': 'TAC312', },
    {'name': 'TAC 312 USA NO NETS!!!', 'tg': 312, 'description': 'TAC312', },
    {'name': 'TAC313', 'tg': 313, 'description': 'TAC314', },
    {'name': 'TAC 313 USA NO NETS!!!', 'tg': 313, 'description': 'TAC314', },
    {'name': 'TAC314', 'tg': 314, 'description': 'TAC314', },
    {'name': 'TAC 314 USA NO NETS!!!', 'tg': 314, 'description': 'TAC314', },
    {'name': 'TAC315', 'tg': 315, 'description': 'TAC315', },
    {'name': 'TAC 315 USA NO NETS!!!', 'tg': 315, 'description': 'TAC315', },
    {'name': 'TAC316', 'tg': 316, 'description': 'TAC316', },
    {'name': 'TAC 316 USA NO NETS!!!', 'tg': 316, 'description': 'TAC316', },
    {'name': 'TAC317', 'tg': 317, 'description': 'TAC317', },
    {'name': 'TAC 317 USA NO NETS!!!', 'tg': 317, 'description': 'TAC318', },
    {'name': 'TAC318', 'tg': 318, 'description': 'TAC318', },
    {'name': 'TAC 318 USA NO NETS!!!', 'tg': 318, 'description': 'TAC318', },
    {'name': 'TAC319', 'tg': 319, 'description': 'TAC319', },
    {'name': 'TAC 319 USA NO NETS!!!', 'tg': 319, 'description': 'TAC319', },
    {'name': 'USA', 'tg': 1776, 'description': 'USA 1776', },
    {'name': '1776', 'tg': 1776, 'description': 'USA 1776', },
    {'name': '3020', 'tg': 3020, 'description': 'Newfoundland & Labrador CA', },
    {'name': 'Newfoundland & Labrador', 'tg': 3020, 'description': 'Newfoundland & Labrador CA', },
    {'name': '3021', 'tg': 3021, 'description': 'Nova Scotia CA', },
    {'name': 'Nova Scotia', 'tg': 3021, 'description': 'Nova Scotia CA', },
    {'name': 'Quebec', 'tg': 3022, 'description': 'Quebec CA', },
    {'name': 'Ontario', 'tg': 3023, 'description': 'Ontario CA', },
    {'name': 'Bridge', 'tg': 3100, 'description': 'Bridge', },
    {'name': 'USA Bridge', 'tg': 3100, 'description': 'Bridge', },
    {'name': 'Alabama', 'tg': 3101, 'description': 'Alabama State-wide', },
    {'name': 'PAPA Chat', 'tg': 31077, 'description': 'PAPA Chat', },
    {'name': 'Florida - 10 Minute Limit', 'tg': 3112, 'description': 'Florida State-wide', },
    {'name': 'Georgia', 'tg': 3113, 'description': 'Georgia State-wide', },
    {'name': 'Georgia - 10 Minute Limit', 'tg': 3113, 'description': 'Georgia State-wide', },
    {'name': 'Idaho', 'tg': 3116, 'description': 'Idaho State-wide', },
    {'name': 'Idaho - 10 Minute Limit', 'tg': 3116, 'description': 'Idaho State-wide', },
    {'name': 'Maryland - 10 Minute Limit', 'tg': 3124, 'description': 'Maryland State-wide', },
    {'name': 'Maryland', 'tg': 3124, 'description': 'Maryland State-wide', },
    {'name': 'South Carolina - 10 Minute Limit', 'tg': 3145, 'description': 'South Carolina State-wide', },
    {'name': 'North Carolina - 10 Minute Limit', 'tg': 3137, 'description': 'North Carolina State-Wide', },
    {'name': 'Tennessee', 'tg': 3147, 'description': 'Tennessee State-wide', },
    {'name': 'Tennessee - 10 Minute Limit', 'tg': 3147, 'description': 'Tennessee State-wide', },
    {'name': 'Texas', 'tg': 3148, 'description': 'Texas State-wide', },
    {'name': 'Texas - 10 Minute Limit', 'tg': 3148, 'description': 'Texas State-wide', },
    {'name': 'VAstate', 'tg': 3151, 'description': 'Virginia State-wide', },
    {'name': 'WIstate', 'tg': 3155, 'description': 'Wisconsin State-wide', },
    {'name': 'Wyoming', 'tg': 3156, 'description': 'Wyoming State-wide', },
    {'name': 'Wyoming - 10 Minute Limit', 'tg': 3156, 'description': 'Wyoming State-wide', },
    {'name': 'Wyoming Severe WX', 'tg': 31563, 'description': 'Wyoming Severe WX', },
    {'name': 'Central Wyoming', 'tg': 31567, 'description': 'Central Wyoming', },
    {'name': 'CAP', 'tg': 3160, 'description': 'Civil Air Patrol', },
    {'name': 'MWreg', 'tg': 3169, 'description': 'Midwest Region ND SD NE MN IA MO WI IL MI IN OH', },
    {'name': 'NoCo', 'tg': 3171, 'description': 'NoCo', },
    {'name': 'NEreg', 'tg': 3172, 'description': 'Northeast Region NY NJ VT MA CT NH RI ME', },
    {'name': 'MAreg', 'tg': 3173, 'description': 'Mid-Atlantic Region PA WV VA MD DE DC', },
    {'name': 'SEreg', 'tg': 3174, 'description': 'Southeast Region AR LA KY TN MS AL GA FL NC SC', },
    {'name': 'Southeast', 'tg': 3174, 'description': 'Southeast Region AR LA KY TN MS AL GA FL NC SC', },
    {'name': 'SPreg', 'tg': 3175, 'description': 'Southern Plains Region KS OK TX', },
    {'name': 'SWreg', 'tg': 3176, 'description': 'Southwest Region CA NV AZ NM HI', },
    {'name': 'MTreg', 'tg': 3177, 'description': 'Mountain Region AK WA OR ID MT WY UT CO', },
    {'name': 'Fusion', 'tg': 3182, 'description': 'Fusion', },
    {'name': 'Cactus', 'tg': 3185, 'description': 'Cactus', },
    {'name': 'US Hurricane Net', 'tg': 3199, 'description': 'US Hurricane Net', },
    {'name': 'Disconnect', 'tg': 4000, 'description': 'Brandmeister Disconnect', },
    {'name': 'Mil Vets', 'tg': 98008, 'description': 'Military Veterans', },
    {'name': 'Parrot - Private Call ONLY', 'tg': 9990, 'description': 'Parrot - Private Call ONLY', },
    {'name': '9990', 'tg': 9990, 'description': 'Parrot - Private Call ONLY', },
    {'name': 'FlexRadio SIG', 'tg': 30234, 'description': 'FlexRadio SIG', },
    {'name': 'PAPA Bridge', 'tg': 31078, 'description': 'Papa Bridge', },
    {'name': 'QuadNet', 'tg': 31012, 'description': 'QuadNet', },
    {'name': 'First Coast DMR', 'tg': 31121, 'description': 'First Coast', },
    {'name': 'FL State ARES', 'tg': 31127, 'description': 'FL State ARES', },
    {'name': 'KSC Kennedy Space Center', 'tg': 311274, 'description': 'KSC Kennedy Space Center', },
    {'name': 'GA ARES', 'tg': 31130, 'description': 'Georgia ARES', },
    {'name': 'Georgia ARES', 'tg': 31130, 'description': 'Georgia ARES', },
    {'name': 'Atlanta Metro', 'tg': 31131, 'description': 'Atlanta Metro', },
    {'name': 'South Georgia', 'tg': 31132, 'description': 'South Georgia', },
    {'name': 'SETN NWGA', 'tg': 31133, 'description': 'SE Tennessee/NW Georgia', },
    {'name': 'North Georgia', 'tg': 31134, 'description': 'North Georgia', },
    {'name': 'Central GA', 'tg': 31135, 'description': 'Central Georgia', },
    {'name': 'Southwest GA', 'tg': 31136, 'description': 'Southwest Georgia', },
    {'name': 'KingsLand Digital', 'tg': 31137, 'description': 'Kingsland Digital', },
    {'name': 'Georgia Skywarn', 'tg': 31139, 'description': 'Georgia Skywarn', },
    {'name': 'NY-NJ-PA TriState', 'tg': 31360, 'description': 'NY-NJ-PA TriState', },
    {'name': 'Tidewater VA', 'tg': 31515, 'description': 'Tidewater VA', },
    {'name': 'America-Link', 'tg': 31656, 'description': 'America Link', },
    {'name': 'TGIF', 'tg': 31665, 'description': 'TGIF Network', },
    {'name': 'Handi-Hams', 'tg': 31990, 'description': 'Handi-Hams', },
    {'name': 'Hamfurs', 'tg': 98002, 'description': 'Hamfurs', },
    {'name': 'Reddit', 'tg': 98003, 'description': 'Reddit', },
    {'name': 'Vidalia Net', 'tg': 310592, 'description': 'Vidalia Net', },
    {'name': 'Kingsland Digital', 'tg': 311307, 'description': 'Kingsland Digital', },
    {'name': 'BSRG', 'tg': 311340, 'description': 'BSRG', },
    {'name': 'N1KDO Group', 'tg': 3113090, 'description': 'N1KDO Group Call', },
    {'name': 'AllCall', 'tg': 16777215, 'description': 'All Call (don\'t!)', },
]

talk_groups['DMR-MARC'] = [
    {'name': 'DMR-MARC NA', 'tg': 1, 'description': 'DMR-MARC North America', },
    {'name': 'North America', 'tg': 1, 'description': 'DMR-MARC North America', },
    {'name': 'DMR-MARC WW', 'tg': 3, 'description': 'DMR-MARC World-wide', },
    {'name': 'Worldwide', 'tg': 3, 'description': 'DMR-MARC World-wide', },
    {'name': 'TriState IL IN WI', 'tg': 8, 'description': 'DMR-MARC TriState IL IN WI', },
    {'name': 'DMR-MARC WWE', 'tg': 13, 'description': 'World-wide English', },
    {'name': 'DMRplus UK', 'tg': 435, 'description': 'DMR+ O+UK', },
    {'name': 'DMR-MARC MWreg', 'tg': 3169, 'description': 'Midwest Region ND SD NE MN IA MO WI IL MI IN OH', },
    {'name': 'DMR-MARC SEreg', 'tg': 3174, 'description': 'Southeast Region AR LA KY TN MS AL GA FL NC SC', },
    {'name': 'DMR-MARC SPreg', 'tg': 3175, 'description': 'Southern Plains Region KS OK TX', },
    {'name': 'DMR-MARC SWreg', 'tg': 3176, 'description': 'Southwest Region CA NV AZ NM HI', },
]

talk_groups['DMR-SE'] = [
    {'name': 'DMR-MARC NA', 'tg': 1, 'description': 'DMR-MARC North America', },
    #  {'name': 'Local2', 'tg': 2, 'description': 'Local 2', },
    {'name': 'First Coast', 'tg': 2, 'description': 'First Coast', },
    {'name': 'DMR-MARC WW', 'tg': 3, 'description': 'DMR-MARC Worldwide', },
    {'name': 'ATL Metro', 'tg': 8, 'description': 'Atlanta Metro', },
    {'name': 'Local8', 'tg': 8, 'description': 'Local 8', },
    {'name': 'Local9', 'tg': 9, 'description': 'Local 9', },
    {'name': 'WWGC', 'tg': 10, 'description': 'World-wide German', },
    {'name': 'DMR-MARC WWE', 'tg': 13, 'description': 'World-wide English', },
    {'name': 'WWSC', 'tg': 14, 'description': 'World-wide Spanish', },
    {'name': 'BM-WW', 'tg': 91, 'description': 'BM Worldwide', },
    {'name': 'BM-NA', 'tg': 93, 'description': 'BM North America', },
    {'name': 'DMRpUSA', 'tg': 133, 'description': 'DMR+ USA', },
    {'name': 'TAC310', 'tg': 310, 'description': 'TAC310', },
    {'name': 'TAC311', 'tg': 311, 'description': 'TAC311', },
    {'name': 'TAC312', 'tg': 312, 'description': 'TAC312', },
    {'name': 'TAC313', 'tg': 313, 'description': 'TAC313', },
    {'name': 'TAC314', 'tg': 314, 'description': 'TAC314', },
    {'name': 'TAC315', 'tg': 315, 'description': 'TAC315', },
    {'name': 'TAC316', 'tg': 316, 'description': 'TAC316', },
    {'name': 'TAC317', 'tg': 317, 'description': 'TAC317', },
    {'name': 'TAC318', 'tg': 318, 'description': 'TAC318', },
    {'name': 'TAC319', 'tg': 319, 'description': 'TAC319', },
    {'name': 'USA', 'tg': 1776, 'description': 'USA 1776', },
    {'name': 'Bridge', 'tg': 3100, 'description': 'Bridge 3100', },
    {'name': 'DEstate', 'tg': 3110, 'description': 'Delaware State-wide', },
    {'name': 'DCstate', 'tg': 3111, 'description': 'District of Columbia', },
    {'name': 'Florida', 'tg': 3112, 'description': 'Florida State-wide', },
    {'name': 'GAstate', 'tg': 3113, 'description': 'Georgia State-wide', },
    {'name': 'INstate', 'tg': 3118, 'description': 'Indiana State-wide', },
    {'name': 'KYstate', 'tg': 3121, 'description': 'Kentucky State-wide', },
    {'name': 'MDstate', 'tg': 3124, 'description': 'Maryland State-wide', },
    {'name': 'MAstate', 'tg': 3125, 'description': 'Massachusetts State-wide', },
    {'name': 'MIstate', 'tg': 3126, 'description': 'Michigan State-wide', },
    {'name': 'MNstate', 'tg': 3127, 'description': 'Minnesota State-wide', },
    {'name': 'NHstate', 'tg': 3133, 'description': 'New Hampshire State-wide', },
    {'name': 'NYstate', 'tg': 3136, 'description': 'New York State-wide', },
    {'name': 'NCstate', 'tg': 3137, 'description': 'North Carolina State-Wide', },
    {'name': 'OHstate', 'tg': 3139, 'description': 'Ohio State-wide', },
    {'name': 'PAstate', 'tg': 3142, 'description': 'Pennsylvania State-wide', },
    {'name': 'SCstate', 'tg': 3145, 'description': 'South Carolina State-wide', },
    {'name': 'TNstate', 'tg': 3147, 'description': 'Tennessee State-wide', },
    {'name': 'TXstate', 'tg': 3148, 'description': 'Texas State-wide', },
    {'name': 'VAstate', 'tg': 3151, 'description': 'Virginia State-wide', },
    {'name': 'WIstate', 'tg': 3155, 'description': 'Wisconsin State-wide', },
    {'name': 'MWreg', 'tg': 3169, 'description': 'Midwest Region ND SD NE MN IA MO WI IL MI IN OH', },
    {'name': 'NEreg', 'tg': 3172, 'description': 'Northeast Region NY NJ VT MA CT NH RI ME', },
    {'name': 'MAreg', 'tg': 3173, 'description': 'Mid-Atlantic Region PA WV VA MD DE DC', },
    {'name': 'DMR-MARC SEreg', 'tg': 3174, 'description': 'Southeast Region AR LA KY TN MS AL GA FL NC SC', },
    {'name': 'SPreg', 'tg': 3175, 'description': 'Southern Plains Region KS OK TX', },
    {'name': 'SWreg', 'tg': 3176, 'description': 'Southwest Region CA NV AZ NM HI', },
    {'name': 'MTreg', 'tg': 3177, 'description': 'Mountain Region AK WA OR ID MT WY UT CO', },
    {'name': 'Fusion', 'tg': 3182, 'description': 'Fusion', },
    {'name': 'Cactus', 'tg': 3185, 'description': 'Cactus', },
    {'name': 'PRN2', 'tg': 7762, 'description': 'PRN2', },
    {'name': 'Dillo', 'tg': 8484, 'description': 'Dillo', },
    {'name': 'Crossroads', 'tg': 8710, 'description': 'Crossroads Indiana', },
    {'name': 'TAC1', 'tg': 8951, 'description': 'TAC1', },
    {'name': 'Parrot', 'tg': 9998, 'description': 'Parrot', },
    {'name': 'NE Region BM', 'tg': 13172, 'description': 'NE Region BM', },
    {'name': 'SE Region BM', 'tg': 13174, 'description': 'SE Region BM', },
    {'name': 'QuadNet', 'tg': 31012, 'description': 'QuadNet', },
    #  {'name': 'First Coast', 'tg': 31121, 'description': 'First Coast', },
    {'name': 'NE FL ARES', 'tg': 31128, 'description': 'NE FL ARES', },
    {'name': 'GA ARES', 'tg': 31130, 'description': 'Georgia ARES', },
    {'name': 'ATL Metro', 'tg': 31131, 'description': 'Atlanta Metro', },
    {'name': 'GA South', 'tg': 31132, 'description': 'Georgia South', },
    {'name': 'GA North', 'tg': 31134, 'description': 'Georgia North', },
    {'name': 'Kingsland Digital', 'tg': 31137, 'description': 'Kingsland Digital', },
    {'name': 'GA Skywarn', 'tg': 31139, 'description': 'Georgia Skywarn', },
    {'name': 'TGIF', 'tg': 31665, 'description': 'TGIF Network', },
    {'name': 'Handi-Hams', 'tg': 31990, 'description': 'Handi-Hams', },
    {'name': 'Vidalia Net', 'tg': 310592, 'description': 'Vidalia Net', },
    {'name': 'Vdalia Net', 'tg': 310592, 'description': 'Vidalia Net', },  # typo!
    {'name': 'Kingsland 9', 'tg': 311307, 'description': 'Kingland Local 9', },
    {'name': 'Waycross 9', 'tg': 311350, 'description': 'Waycross Local 9', },
    {'name': 'TNTEN', 'tg': 314710, 'description': 'Tennessee Ten', },
    {'name': 'AllCall', 'tg': 16777215, 'description': 'All Call (don\'t!)', },
]

talk_groups['K4USD'] = [
    {'name': 'DMR-MARC NA', 'tg': 1, 'description': 'DMR-MARC North America', },
    {'name': 'Local2', 'tg': 2, 'description': 'Local 2', },
    {'name': 'DMR-MARC WW', 'tg': 3, 'description': 'DMR-MARC World-wide', },
    {'name': 'ATL Metro', 'tg': 8, 'description': 'Atlanta Metro', },
    {'name': 'Local8', 'tg': 8, 'description': 'Local 8', },
    {'name': 'Local9', 'tg': 9, 'description': 'Local 9', },
    {'name': 'WWGC', 'tg': 10, 'description': 'World-wide German', },
    {'name': 'DMR-MARC WWE', 'tg': 13, 'description': 'World-wide English', },
    {'name': 'WWSC', 'tg': 14, 'description': 'World-wide Spanish', },
    {'name': 'BM-WW', 'tg': 91, 'description': 'Brandmeister Worldwide', },
    {'name': 'BM-NA', 'tg': 93, 'description': 'Brandmeister North America', },
    {'name': 'DMRpUSA', 'tg': 133, 'description': 'DMR+ USA', },
    {'name': 'TAC310', 'tg': 310, 'description': 'TAC310', },
    {'name': 'TAC311', 'tg': 311, 'description': 'TAC311', },
    {'name': 'TAC312', 'tg': 312, 'description': 'TAC312', },
    {'name': 'TAC313', 'tg': 313, 'description': 'TAC313', },
    {'name': 'TAC314', 'tg': 314, 'description': 'TAC314', },
    {'name': 'TAC315', 'tg': 315, 'description': 'TAC315', },
    {'name': 'TAC316', 'tg': 316, 'description': 'TAC316', },
    {'name': 'TAC317', 'tg': 317, 'description': 'TAC317', },
    {'name': 'TAC318', 'tg': 318, 'description': 'TAC318', },
    {'name': 'TAC319', 'tg': 319, 'description': 'TAC319', },
    {'name': 'JOTA', 'tg': 907, 'description': 'Georgia State-wide', },
    {'name': 'USA', 'tg': 1776, 'description': 'USA 1776', },
    {'name': 'Bridge', 'tg': 3100, 'description': 'Bridge 3100', },
    {'name': 'DEstate', 'tg': 3110, 'description': 'Delaware State-wide', },
    {'name': 'DCstate', 'tg': 3111, 'description': 'District of Columbia', },
    {'name': 'FLstate', 'tg': 3112, 'description': 'Florida State-wide', },
    {'name': 'Georgia', 'tg': 3113, 'description': 'Georgia State-wide', },
    {'name': 'INstate', 'tg': 3118, 'description': 'Indiana State-wide', },
    {'name': 'KYstate', 'tg': 3121, 'description': 'Kentucky State-wide', },
    {'name': 'MDstate', 'tg': 3124, 'description': 'Maryland State-wide', },
    {'name': 'MAstate', 'tg': 3125, 'description': 'Massachusetts State-wide', },
    {'name': 'MIstate', 'tg': 3126, 'description': 'Michigan State-wide', },
    {'name': 'MNstate', 'tg': 3127, 'description': 'Minnesota State-wide', },
    {'name': 'NHstate', 'tg': 3133, 'description': 'New Hampshire State-wide', },
    {'name': 'NYstate', 'tg': 3136, 'description': 'New York State-wide', },
    {'name': 'NCstate', 'tg': 3137, 'description': 'North Carolina State-Wide', },
    {'name': 'OHstate', 'tg': 3139, 'description': 'Ohio State-wide', },
    {'name': 'PAstate', 'tg': 3142, 'description': 'Pennsylvania State-wide', },
    {'name': 'SCstate', 'tg': 3145, 'description': 'South Carolina State-wide', },
    {'name': 'TNstate', 'tg': 3147, 'description': 'Tennessee State-wide', },
    {'name': 'TXstate', 'tg': 3148, 'description': 'Texas State-wide', },
    {'name': 'VAstate', 'tg': 3151, 'description': 'Virginia State-wide', },
    {'name': 'WIstate', 'tg': 3155, 'description': 'Wisconsin State-wide', },
    {'name': 'MWreg', 'tg': 3169, 'description': 'Midwest Region ND SD NE MN IA MO WI IL MI IN OH', },
    {'name': 'NEreg', 'tg': 3172, 'description': 'Northeast Region NY NJ VT MA CT NH RI ME', },
    {'name': 'MAreg', 'tg': 3173, 'description': 'Mid-Atlantic Region PA WV VA MD DE DC', },
    {'name': 'SEreg', 'tg': 3174, 'description': 'Southeast Region AR LA KY TN MS AL GA FL NC SC', },
    {'name': 'SPreg', 'tg': 3175, 'description': 'Southern Plains Region KS OK TX', },
    {'name': 'SWreg', 'tg': 3176, 'description': 'Southwest Region CA NV AZ NM HI', },
    {'name': 'MTreg', 'tg': 3177, 'description': 'Mountain Region AK WA OR ID MT WY UT CO', },
    {'name': 'Fusion', 'tg': 3182, 'description': 'Fusion', },
    {'name': 'Cactus', 'tg': 3185, 'description': 'Cactus', },
    {'name': 'PRN2', 'tg': 7762, 'description': 'PRN2', },
    {'name': 'Dillo', 'tg': 8484, 'description': 'Dillo', },
    {'name': 'Crossroads', 'tg': 8710, 'description': 'Crossroads Indiana', },
    {'name': 'TAC1', 'tg': 8951, 'description': 'TAC1', },
    {'name': 'Parrot', 'tg': 9998, 'description': 'Parrot', },
    {'name': 'QuadNet', 'tg': 31012, 'description': 'QuadNet', },
    {'name': 'First Coast', 'tg': 31121, 'description': 'First Coast', },
    {'name': 'GA ARES', 'tg': 31130, 'description': 'Georgia ARES', },
    {'name': 'ATL Metro BM', 'tg': 31131, 'description': 'Atlanta Metro BM', },
    {'name': 'GA North', 'tg': 31134, 'description': 'Georgia North', },
    {'name': 'GA Skywarn', 'tg': 31139, 'description': 'Georgia Skywarn', },
    {'name': 'TGIF', 'tg': 31665, 'description': 'TGIF Network', },
    {'name': 'Handi-Hams', 'tg': 31990, 'description': 'Handi-Hams', },
    {'name': 'Vidalia Net', 'tg': 310592, 'description': 'Vidalia Net', },
    {'name': 'Vdalia Net', 'tg': 310592, 'description': 'Vidalia Net', }, # typo!
    {'name': 'TNTEN', 'tg': 314710, 'description': 'Tennessee Ten', },
    {'name': 'AllCall', 'tg': 16777215, 'description': 'All Call (don\'t!)', },
]

talk_groups['Ham Digital'] = [
    {'name': 'Worldwide', 'tg': 1, 'description': 'DMR-MARC Worldwide', },
    {'name': 'Local2', 'tg': 2, 'description': 'Local 2', },
    {'name': 'North America', 'tg': 3, 'description': 'DMR-MARC North America', },
    #{'name': 'ATL Metro', 'tg': 8, 'description': 'Atlanta Metro', },
    {'name': 'Atlanta Metro', 'tg': 8, 'description': 'Atlanta Metro', },
    {'name': 'TriState IL IN WI', 'tg': 8, 'description': 'DMR-MARC TriState IL IN WI', },
    {'name': 'Local9', 'tg': 9, 'description': 'Local 9', },
    {'name': 'WWGC', 'tg': 10, 'description': 'World-wide German', },
    {'name': 'Worldwide English', 'tg': 13, 'description': 'World-wide English', },
    {'name': 'WWSC', 'tg': 14, 'description': 'World-wide Spanish', },
    #{'name': 'BM-WW', 'tg': 91, 'description': 'BM Worldwide', },
    {'name': 'BM Worldwide', 'tg': 91, 'description': 'BM Worldwide', },
    #{'name': 'BM-NA', 'tg': 93, 'description': 'BM North America', },
    {'name': 'BM North America', 'tg': 93, 'description': 'BM North America', },
    {'name': 'Worldwide English', 'tg': 113, 'description': 'Worldwide English', },
    {'name': 'Worldwide Spanish', 'tg': 114, 'description': 'Worldwide Spanish', },
    {'name': 'DMRpUSA', 'tg': 133, 'description': 'DMR+ USA', },
    {'name': 'TAC 310', 'tg': 310, 'description': 'TAC310', },
    {'name': 'TAC 311', 'tg': 311, 'description': 'TAC311', },
    {'name': 'TAC 312', 'tg': 312, 'description': 'TAC312', },
    {'name': 'TAC 313', 'tg': 313, 'description': 'TAC313', },
    {'name': 'TAC 314', 'tg': 314, 'description': 'TAC314', },
    {'name': 'TAC 315', 'tg': 315, 'description': 'TAC315', },
    {'name': 'TAC 316', 'tg': 316, 'description': 'TAC316', },
    {'name': 'TAC 317', 'tg': 317, 'description': 'TAC317', },
    {'name': 'TAC 318', 'tg': 318, 'description': 'TAC318', },
    {'name': 'TAC 319', 'tg': 319, 'description': 'TAC319', },
    {'name': 'JOTA', 'tg': 907, 'description': 'Georgia State-wide', },
    {'name': 'USA', 'tg': 1776, 'description': 'USA 1776', },
    # {'name': 'Bridge', 'tg': 3100, 'description': 'Bridge 3100', },
    {'name': 'BM USA Bridge', 'tg': 3100, 'description': 'Bridge 3100', },
    {'name': 'Alabama', 'tg': 3101, 'description': 'Alabama State-wide', },
    {'name': 'DEstate', 'tg': 3110, 'description': 'Delaware State-wide', },
    {'name': 'DCstate', 'tg': 3111, 'description': 'District of Columbia', },
    {'name': 'FLstate', 'tg': 3112, 'description': 'Florida State-wide', },
    {'name': 'Florida', 'tg': 3112, 'description': 'Florida State-wide', },
    {'name': 'GAstate', 'tg': 3113, 'description': 'Georgia State-wide', },
    {'name': 'Georgia', 'tg': 3113, 'description': 'Georgia State-wide', },
    {'name': 'INstate', 'tg': 3118, 'description': 'Indiana State-wide', },
    {'name': 'KYstate', 'tg': 3121, 'description': 'Kentucky State-wide', },
    {'name': 'MDstate', 'tg': 3124, 'description': 'Maryland State-wide', },
    {'name': 'MAstate', 'tg': 3125, 'description': 'Massachusetts State-wide', },
    {'name': 'MIstate', 'tg': 3126, 'description': 'Michigan State-wide', },
    {'name': 'MNstate', 'tg': 3127, 'description': 'Minnesota State-wide', },
    {'name': 'NHstate', 'tg': 3133, 'description': 'New Hampshire State-wide', },
    {'name': 'NYstate', 'tg': 3136, 'description': 'New York State-wide', },
    {'name': 'NCstate', 'tg': 3137, 'description': 'North Carolina State-Wide', },
    {'name': 'OHstate', 'tg': 3139, 'description': 'Ohio State-wide', },
    {'name': 'PAstate', 'tg': 3142, 'description': 'Pennsylvania State-wide', },
    {'name': 'SCstate', 'tg': 3145, 'description': 'South Carolina State-wide', },
    {'name': 'TNstate', 'tg': 3147, 'description': 'Tennessee State-wide', },
    {'name': 'TXstate', 'tg': 3148, 'description': 'Texas State-wide', },
    {'name': 'VAstate', 'tg': 3151, 'description': 'Virginia State-wide', },
    {'name': 'WIstate', 'tg': 3155, 'description': 'Wisconsin State-wide', },
    {'name': 'MWreg', 'tg': 3169, 'description': 'Midwest Region ND SD NE MN IA MO WI IL MI IN OH', },
    {'name': 'NEreg', 'tg': 3172, 'description': 'Northeast Region NY NJ VT MA CT NH RI ME', },
    {'name': 'MAreg', 'tg': 3173, 'description': 'Mid-Atlantic Region PA WV VA MD DE DC', },
    {'name': 'SEreg', 'tg': 3174, 'description': 'Southeast Region AR LA KY TN MS AL GA FL NC SC', },
    {'name': 'SPreg', 'tg': 3175, 'description': 'Southern Plains Region KS OK TX', },
    {'name': 'SWreg', 'tg': 3176, 'description': 'Southwest Region CA NV AZ NM HI', },
    {'name': 'MTreg', 'tg': 3177, 'description': 'Mountain Region AK WA OR ID MT WY UT CO', },
    {'name': 'Fusion', 'tg': 3182, 'description': 'Fusion', },
    {'name': 'Cactus', 'tg': 3185, 'description': 'Cactus', },
    {'name': 'TAC1', 'tg': 8951, 'description': 'TAC1', },
    {'name': 'JOTA TAC1', 'tg': 9071, 'description': 'JOTA TAC1', },
    {'name': 'JOTA TAC2', 'tg': 9072, 'description': 'JOTA TAC2', },
    {'name': 'Disconnect', 'tg': 4000, 'description': 'Brandmeister Disconnect', },
    {'name': 'Parrot', 'tg': 9998, 'description': 'Parrot', },
    {'name': 'Alabama Link', 'tg': 31010, 'description': 'Alabama Link', },
    {'name': 'QuadNet', 'tg': 31012, 'description': 'QuadNet', },
    {'name': 'First Coast', 'tg': 31121, 'description': 'First Coast', },
    {'name': 'Georgia ARES', 'tg': 31130, 'description': 'Georgia ARES', },
    {'name': 'ATL Metro BM', 'tg': 31131, 'description': 'Atlanta Metro BM', },
    {'name': 'North Georgia', 'tg': 31134, 'description': 'Georgia North', },
    {'name': 'GA Skywarn', 'tg': 31139, 'description': 'Georgia Skywarn', },
    {'name': 'NY-NJ-PA TriState', 'tg': 31360, 'description': 'NY-NJ-PA TriState', },
    {'name': 'Texas-Nexus', 'tg': 31488, 'description': 'Texas-Nexus', },
    {'name': 'Tidewater VA', 'tg': 31515, 'description': 'Tidewater VA', },
    {'name': 'TGIF', 'tg': 31665, 'description': 'TGIF Network', },
    {'name': 'Handi-Hams', 'tg': 31990, 'description': 'Handi-Hams', },
    {'name': 'TNTEN', 'tg': 314710, 'description': 'Tennessee Ten', },
    {'name': 'AllCall', 'tg': 16777215, 'description': 'All Call (don\'t!)', },
]

new_master_dict = {}
for network in networks:
    for talk_group in talk_groups[network]:
        tg = talk_group['tg']
        tg_name = talk_group['name']
        if tg not in new_master_dict:
            new_master_dict[tg] = {'name': tg_name,
                                   'desc': talk_group['description'],
                                   'aliases': {network: [tg_name]},
                                   }
        else:
            new_master_tg_dict = new_master_dict[tg]
            aliases = new_master_tg_dict['aliases']
            if network not in aliases:
                aliases[network] = [tg_name]
            else:
                aliases[network].append(tg_name)

with open('talkgroups.json', 'w') as outfile:
    json.dump(new_master_dict, outfile, indent=2)

talk_group_alias_to_number_dict = {}
talk_group_number_to_name_dict = {}
talk_group_network_number_to_name_dict = {}

for k, v in new_master_dict.items():
    aliases_dict = v.get('aliases', {})
    for network, aliases in aliases_dict.items():
        if network not in talk_group_alias_to_number_dict:
            talk_group_alias_to_number_dict[network] = {}
        if network not in talk_group_network_number_to_name_dict:
            talk_group_network_number_to_name_dict[network] = {}
        for alias in aliases:
            if alias not in talk_group_alias_to_number_dict[network]:
                talk_group_alias_to_number_dict[network][alias] = k
        talk_group_network_number_to_name_dict[network][k] = aliases[0]

    talk_group_number_to_name_dict[k] = v.get('name', str(k))

talk_group_name_to_number_mapping = {}
talk_group_number_to_data_mapping = {}

for network in networks:
    talk_group_name_to_number_mapping[network] = {}
    talk_group_number_to_data_mapping[network] = {}
    for talk_group in talk_groups[network]:
        talk_group_name_to_number_mapping[network][talk_group['name']] = talk_group
        talk_group_number_to_data_mapping[network][talk_group['tg']] = talk_group
