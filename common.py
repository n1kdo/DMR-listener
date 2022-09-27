import logging
import re

# all traffic to these talk groups will be logged.
interesting_talk_group_names = [
    'ATL Metro',
    #  'Bridge',
    'GAstate',
    'GA ARES',
    'GA North',
    'GA Skywarn',
    "SEreg",
    #"Vdalia Net",
    #"Vidalia Net",
]

# all traffic from the interesting peers will be logged.  Best to not turn on brandmeister.
interesting_peer_ids = [
    #-1,      # brandmeister
    #-3102,   # brandmeister
    #-3104,   # brandmeister
    310293,  # w4boc  stone mountain
    310371,  # w4doc  atlanta
    310466,  # k4vyx  savannah
    310592,  # KG4BKO vidalia
    310969,  # W4KST  Marietta
    310996,  # KM4EYX Douglas GA (NEW)
    311303,  # KE4OKD Sandy Springs
    311313,  # w8red  snellville
    311314,  # KD4KHO Canton
    311318,  # K4QHR  Kingsland
    311320,  # w4cba  cumming
    311321,  # n4taw  between
    311322,  # ka3jij gainesville
    311337,  # wa4asi covington
    311338,  # kd4z   sweat mountain
    311350,  # km4dnd waycross
    311617,  # ke4pmp Parrot GA
    311637,  # NG4RF  Cumming
    312243,  # WA4OKJ Rome
    312284,  # KD4IEZ Dublin
    312288,  # AF1G   Kathleen
    312384,  # KZ4FOX Athens
    312391,  # KE4PMP Cochran
    312429,  # KE4RJI Tifton
    312444,  # KZ4FOX Athens
    312477,  # WX4EMA Macon
]

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
    s = s.strip()
    if len(s) < 1:
        logging.warning('talkgroup name filter problem: {} -> {}'.format(tg_name, s))
    return s


networks = ['Brandmeister', 'DMR-MARC', 'DMR-SE', 'K4USD', 'Ham Digital']

site_name_to_network_map = {'BM-US-3102': 'Brandmeister',
                            'DMR-MARC-CCEAST': 'DMR-MARC',
                            'DMR-MARC-CCWEST': 'DMR-MARC',
                            'DMR-SE': 'DMR-SE',
                            'K4USD Network': 'K4USD',
                            'K4USD-2 Network': 'K4USD',
                            'Ham Digital': 'Ham Digital',
                            }

""" 
mapping of C-bridge talkgroup name to talkgroup number to description
"""
talk_groups = {}

talk_groups['DMR-MARC'] = [
    {'name': 'DMR-MARC NA', 'tg': 1, 'description': 'DMR-MARC North America', },
    {'name': 'DMR-MARC WW', 'tg': 3, 'description': 'DMR-MARC World-wide', },
    {'name': 'DMR-MARC WWE', 'tg': 13, 'description': 'World-wide English', },
    {'name': 'DMR-MARC SEreg', 'tg': 3174, 'description': 'Southeast Region AR LA KY TN MS AL GA FL NC SC', },
]

talk_groups['DMR-SE'] = [
    {'name': 'DMR-MARC NA', 'tg': 1, 'description': 'DMR-MARC North America', },
    #  {'name': 'Local2', 'tg': 2, 'description': 'Local 2', },
    {'name': 'First Coast', 'tg': 2, 'description': 'First Coast', },
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
    {'name': 'USA', 'tg': 1776, 'description': 'USA 1776', },
    {'name': 'Bridge', 'tg': 3100, 'description': 'Bridge 3100', },
    {'name': 'DEstate', 'tg': 3110, 'description': 'Delaware State-wide', },
    {'name': 'DCstate', 'tg': 3111, 'description': 'District of Columbia', },
    {'name': 'FLstate', 'tg': 3112, 'description': 'Florida State-wide', },
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

talk_groups['Brandmeister'] = [
    {'name': 'Local2', 'tg': 2, 'description': 'Local 2', },
    {'name': '2', 'tg': 2, 'description': 'Local 2', },
    {'name': 'Local8', 'tg': 8, 'description': 'Local 8', },
    {'name': 'Regional', 'tg': 8, 'description': 'Local 8', },
    {'name': 'Local', 'tg': 9, 'description': 'Local 9', },
    {'name': 'BM-WW', 'tg': 91, 'description': 'World-wide', },
    {'name': 'World-wide', 'tg': 91, 'description': 'World-wide', },
    {'name': 'BM-NA', 'tg': 93, 'description': 'North America', },
    {'name': 'TAC310', 'tg': 310, 'description': 'TAC310', },
    {'name': 'TAC311', 'tg': 311, 'description': 'TAC311', },
    {'name': 'TAC312', 'tg': 312, 'description': 'TAC312', },
    {'name': 'TAC312', 'tg': 313, 'description': 'TAC314', },
    {'name': 'TAC312', 'tg': 314, 'description': 'TAC314', },
    {'name': 'TAC312', 'tg': 315, 'description': 'TAC315', },
    {'name': 'TAC312', 'tg': 316, 'description': 'TAC316', },
    {'name': 'TAC312', 'tg': 317, 'description': 'TAC317', },
    {'name': 'TAC312', 'tg': 318, 'description': 'TAC318', },
    {'name': 'TAC312', 'tg': 319, 'description': 'TAC319', },
    {'name': 'USA', 'tg': 1776, 'description': 'USA 1776', },
    {'name': '1776', 'tg': 1776, 'description': 'USA 1776', },
    {'name': 'Bridge', 'tg': 3100, 'description': 'Bridge', },
    {'name': 'USA Bridge', 'tg': 3100, 'description': 'Bridge', },
    {'name': 'DEstate', 'tg': 3110, 'description': 'Delaware State-wide', },
    {'name': 'DCstate', 'tg': 3111, 'description': 'District of Columbia', },
    {'name': 'FLstate', 'tg': 3112, 'description': 'Florida State-wide', },
    {'name': 'GAstate', 'tg': 3113, 'description': 'Georgia State-wide', },
    {'name': 'GaState', 'tg': 3113, 'description': 'Georgia State-wide', },
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
    {'name': 'Southeast', 'tg': 3174, 'description': 'Southeast Region AR LA KY TN MS AL GA FL NC SC', },
    {'name': 'SPreg', 'tg': 3175, 'description': 'Southern Plains Region KS OK TX', },
    {'name': 'SWreg', 'tg': 3176, 'description': 'Southwest Region CA NV AZ NM HI', },
    {'name': 'MTreg', 'tg': 3177, 'description': 'Mountain Region AK WA OR ID MT WY UT CO', },
    {'name': 'Fusion', 'tg': 3182, 'description': 'Fusion', },
    {'name': 'Cactus', 'tg': 3185, 'description': 'Cactus', },
    {'name': 'Disconnect', 'tg': 4000, 'description': 'Brandmeister Disconnect', },
    {'name': 'Parrot', 'tg': 9990, 'description': 'Brandmeister Parrot (private call)', },
    {'name': '9990', 'tg': 9990, 'description': 'Brandmeister Parrot (private call)', },
    {'name': 'PAPA Bridge', 'tg': 31078, 'description': 'Papa Bridge', },
    {'name': 'QuadNet', 'tg': 31012, 'description': 'QuadNet', },
    {'name': 'First Coast', 'tg': 31121, 'description': 'First Coast', },
    {'name': 'GA ARES', 'tg': 31130, 'description': 'Georgia ARES', },
    {'name': 'Georgia ARES', 'tg': 31130, 'description': 'Georgia ARES', },
    {'name': 'ATL Metro', 'tg': 31131, 'description': 'Atlanta Metro', },
    {'name': 'Atlanta Metro', 'tg': 31131, 'description': 'Atlanta Metro', },
    {'name': 'GA North', 'tg': 31134, 'description': 'Georgia North', },
    {'name': 'Central GA', 'tg': 31135, 'description': 'Georgia North', },
    {'name': 'GA Skywarn', 'tg': 31139, 'description': 'Georgia Skywarn', },
    {'name': 'America-Link', 'tg': 31656, 'description': 'America Link', },
    {'name': 'TGIF', 'tg': 31665, 'description': 'TGIF Network', },
    {'name': 'Handi-Hams', 'tg': 31990, 'description': 'Handi-Hams', },
    {'name': 'BSRG', 'tg': 311340, 'description': 'BSRG', },
    {'name': '311340', 'tg': 311340, 'description': 'BSRG', },
    {'name': 'AllCall', 'tg': 16777215, 'description': 'All Call (don\'t!)', },
]

talk_groups['Ham Digital'] = [
    {'name': 'ATL Metro', 'tg': 8, 'description': 'Atlanta Metro', },
    {'name': 'JOTA', 'tg': 907, 'description': 'Georgia State-wide', },
    {'name': 'GAstate', 'tg': 3113, 'description': 'Georgia State-wide', },
    {'name': 'AllCall', 'tg': 16777215, 'description': 'All Call (don\'t!)', },
]

repeaters = [
    # 310293 W4BOC Stone Mountain K4USD
    {'peer_id': '313142', 'call': 'W4BOC', 'input': '446.8125', 'output': '441.8125', 'color_code': '1',
     'location': 'Stone Mountain GA', 'network': 'K4USD',
     'talk_groups': [
         (1, 1, 1),
         (2, 2, 0),
         (3, 1, 1),
         (8, 1, 0),
         (9, 2, 0),
         (13, 1, 1),
         (91, 1, 1),
         (93, 1, 1),
         (133, 1, 1),
         (310, 2, 1),
         (311, 2, 1),
         (312, 2, 1),
         (313, 2, 1),
         (314, 2, 1),
         (315, 2, 1),
         (316, 2, 1),
         (317, 2, 1),
         (318, 2, 1),
         (319, 2, 1),
         (1776, 2, 1),
         (3100, 2, 1),
         (3112, 2, 1),
         (3113, 2, 0),
         (3126, 2, 1),
         (3139, 2, 1),
         (3147, 2, 1),
         (3172, 2, 1),
         (3174, 2, 1),
         (8951, 2, 1),
         (9998, 2, 1),
         (31012, 2, 1),
         (31121, 2, 1),
         (31130, 2, 1),
         (31134, 2, 1),
         (31139, 2, 1),
         (31665, 2, 1),
         (31990, 2, 1),
     ], },
    # 310295 146.73 W4KIP
    {'peer_id': '310295', 'call': 'W4KIP', 'input': '146.130', 'output': '146.730', 'color_code': '1',
     'location': 'Sweat Mountain, Marietta GA', 'network': 'Brandmeister',
     'notes': 'Any Brandmeister talk group may be activated on Time Slot 1',
     'talk_groups': [
         (2, 2, 0),
         (9, 2, 0),
         (91, 1, 1),
         (93, 1, 1),
         (310, 1, 1),
         (311, 1, 1),
         (312, 1, 1),
         (3100, 1, 1),
         (3113, 2, 0),
         (9990, 1, 1),
         (9990, 2, 1),
         (31131, 1, 0),
     ], },
    # 310371 444.825 W4DOC Atlanta
    {'peer_id': '310371', 'call': 'W4DOC', 'input': '449.8250', 'output': '444.8250', 'color_code': '10',
     'location': 'Atlanta GA', 'network': 'K4USD',
     'talk_groups': [
         (1, 1, 1),
         (2, 2, 0),
         (3, 1, 1),
         (8, 1, 0),
         (9, 2, 0),
         (13, 1, 1),
         (91, 1, 1),
         (93, 1, 1),
         (133, 1, 1),
         (310, 2, 1),
         (311, 2, 1),
         (312, 2, 1),
         (313, 2, 1),
         (314, 2, 1),
         (315, 2, 1),
         (316, 2, 1),
         (317, 2, 1),
         (318, 2, 1),
         (319, 2, 1),
         (907, 2, 1),
         (1776, 2, 1),
         (3100, 2, 1),
         (3112, 2, 1),
         (3113, 2, 0),
         (3139, 2, 1),
         (3147, 2, 1),
         (3148, 2, 1),
         (3174, 2, 1),
         (8951, 2, 1),
         (9998, 2, 1),
         (31012, 2, 1),
         (31121, 2, 1),
         (31130, 2, 1),
         (31131, 2, 1),
         (31134, 2, 1),
         (31139, 2, 1),
         (31665, 2, 1),
         (31990, 2, 1),
         (314710, 2, 1),
     ], },
    # 310466 K4VYX Savannah
    {'peer_id': '310466', 'call': 'K4VYX', 'input': '447.8125', 'output': '442.8125', 'color_code': '3',
     'location': 'Savannah GA', 'network': 'DMR-SE', 'notes': '',
     'talk_groups': [
         (1, 1, 1),
         (2, 2, 0),
         (3, 1, 0),
         (9, 1, 0),
         (9, 2, 0),
         (13, 1, 1),
         (91, 1, 1),
         (93, 1, 1),
         (312, 1, 1),
         (317, 1, 1),
         (3100, 1, 1),
         (3112, 1, 1),
         (3113, 1, 0),
         (3139, 1, 1),
         (3147, 1, 1),
         (3174, 1, 0),
         (8951, 1, 1),
         (9998, 1, 1),
         (13172, 1, 1),
         (13174, 1, 1),
         (31130, 1, 1),
         (31131, 1, 1),
         (31132, 1, 1),
         (31137, 1, 1),
         (310592, 1, 1),
         (311350, 1, 1),
     ], },
    # 310592 444.825 KG4BKO Vidalia
    {'peer_id': '310592', 'call': 'KG4BKO', 'input': '449.9875', 'output': '444.9875', 'color_code': '1',
     'location': 'Atlanta GA', 'network': 'DMR-SE',
     'talk_groups': [
         (1, 1, 1),
         (3, 1, 1),
         (3113, 2, 0),
         (31130, 2, 1),
         (31131, 2, 1),
         (310592, 2, 0),
     ], },
    # 310969 W4KST Marietta
    {'peer_id': '310969', 'call': 'W4KST', 'input': '448.275', 'output': '443.275', 'color_code': '7',
     'location': 'KSU Campus Marietta GA', 'network': 'K4USD',
     'talk_groups': [
         (2, 2, 0),
         (9, 2, 0),
         (3113, 2, 0),  # maybe there are more?
     ], },
    # TODO 310996 KM4EYX Douglas GA
    # 311307 W1KFR Kingsland
    {'peer_id': '311307', 'call': 'W1KFR', 'input': '449.625', 'output': '444.625', 'color_code': '3',
     'location': 'Kingsland GA', 'network': 'DMR-SE', 'notes': '',
     'talk_groups': [
         (2, 2, 0),
         (3, 1, 0),
         (9, 1, 0),
         (3112, 1, 1),
         (3113, 1, 0),
         (3174, 1, 0),
         (31128, 1, 0),
         (31131, 1, 1),
         (311307, 1, 0),
     ], },
    # 311313 W8RED Snellville
    {'peer_id': '311313', 'call': 'W8RED', 'input': '447.6000', 'output': '442.6000', 'color_code': '3',
     'location': 'Snellville, GA', 'network': 'K4USD',
     'talk_groups': [
         (1, 1, 1),
         (2, 2, 0),
         (3, 1, 1),
         (8, 1, 0),
         (9, 2, 0),
         (10, 1, 0),
         (13, 1, 1),
         (91, 1, 1),
         (93, 1, 1),
         (133, 1, 1),
         (310, 2, 1),
         (311, 2, 1),
         (312, 2, 1),
         (315, 2, 1),
         (317, 2, 1),
         (319, 2, 1),
         (1776, 2, 1),
         (3100, 2, 1),
         (3113, 2, 0),
         (3174, 2, 1),
         (8951, 2, 1),
         (9998, 2, 1),
         (31012, 2, 1),
         (31665, 2, 1),
         (314710, 2, 1),
     ], },
    # 311314 KD4KHO Canton
    {'peer_id': '311314', 'call': 'KD4KHO', 'input': '439.400', 'output': '434.400', 'color_code': '3',
     'location': 'Canton GA', 'network': 'Brandmeister', 'notes': 'limited coverage',
     'talk_groups': [
         (3113, 1, 0),
         (31130, 2, 0),
         (31131, 2, 0),
         (31134, 2, 0),
     ], },
    # 311318 K4QHR Kingsland
    {'peer_id': '311318', 'call': 'K4QHR', 'input': '447.1125', 'output': '442.1125', 'color_code': '7',
     'location': 'Kingsland GA', 'network': 'DMR-SE', 'notes': '',
     'talk_groups': [
         (1, 1, 1),
         (3112, 2, 1),
         (3113, 2, 0),
         (310592, 2, 0),
     ], },
    # 311321 N4TAW Between
    {'peer_id': '311321', 'call': 'N4TAW', 'input': '448.7375', 'output': '443.7375', 'color_code': '3',
     'location': 'Between GA', 'network': 'K4USD',
     'talk_groups': [
         (1, 1, 1),
         (2, 2, 0),
         (3, 1, 1),
         (8, 1, 0),
         (9, 2, 0),
         (10, 1, 1),
         (13, 1, 1),
         (91, 1, 1),
         (93, 1, 1),
         (310, 2, 1),
         (311, 2, 1),
         (312, 2, 1),
         (1776, 2, 1),
         (3100, 2, 1),
         (3112, 2, 1),
         (3113, 2, 0),
         (3125, 2, 1),
         (3136, 2, 1),
         (3139, 2, 1),
         (3142, 2, 1),
         (3145, 2, 1),
         (3147, 2, 1),
         (3174, 2, 1),
         (8951, 2, 1),
         (9998, 2, 1),
         (31012, 2, 1),
         (31130, 2, 1),
         (31139, 2, 1),
         (31665, 2, 1),
     ], },
    # 311322 KA4JIJ Gainesville
    {'peer_id': '311322', 'call': 'KA3JIJ', 'input': '449.9500', 'output': '444.9500', 'color_code': '1',
     'location': 'Gainesville GA', 'network': 'K4USD',
     'talk_groups': [
         (1, 1, 1),
         (2, 2, 0),
         (3, 1, 1),
         (8, 1, 0),
         (9, 2, 0),
         (13, 1, 1),
         (91, 1, 1),
         (93, 1, 1),
         (133, 1, 1),
         (310, 2, 1),
         (311, 2, 1),
         (312, 2, 1),
         (313, 2, 1),
         (314, 2, 1),
         (315, 2, 1),
         (316, 2, 1),
         (317, 2, 1),
         (318, 2, 1),
         (319, 2, 1),
         (1776, 2, 1),
         (3100, 2, 1),
         (3113, 2, 0),
         (3121, 2, 1),
         (3125, 2, 1),
         (3126, 2, 1),
         (3133, 2, 1),
         (3136, 2, 1),
         (3145, 2, 1),
         (3147, 2, 1),
         (3148, 2, 1),
         (3151, 2, 1),
         (3172, 2, 1),
         (3174, 2, 1),
         (8951, 2, 1),
         (9998, 2, 1),
         (31012, 2, 1),
         (31121, 2, 1),
         (31130, 2, 1),
         (31134, 2, 1),
         (31139, 2, 1),
         (31665, 2, 1),
     ], },
    # 311337 WA4ASI Covington
    {'peer_id': '311337', 'call': 'WA4ASI', 'input': '449.800', 'output': '444.800', 'color_code': '2',
     'location': 'Covington', 'network': 'Brandmeister',
     'notes': 'Any Brandmeister talk group may be activated on Time Slot  1 or 2',
     'talk_groups': [
         (8, 1, 1),
         (91, 1, 1),
         (3113, 2, 0),
         (3174, 2, 0),
     ], },
    # 311338 KD4Z Sweat Mountain
    {'peer_id': '311338', 'call': 'KD4Z', 'input': '447.9750', 'output': '442.9750', 'color_code': '1',
     'location': 'Sweat Mountain GA', 'network': 'Brandmeister',
     'notes': 'Any Brandmeister talk group may be activated on Time Slot 2',
     'talk_groups': [
         (3113, 2, 0),
         (31131, 1, 0),
         (311340, 2, 0),
     ], },
    # 311340 444.775 W4KIP
    {'peer_id': '311340', 'call': 'W4KIP', 'input': '449.775', 'output': '444.775', 'color_code': '1',
     'location': 'Sweat Mountain, Marietta GA', 'network': 'Brandmeister',
     'notes': 'Any Brandmeister talk group may be activated on Time Slot 1',
     'talk_groups': [
         (2, 2, 0),
         (9, 2, 0),
         (91, 1, 1),
         (93, 1, 1),
         (310, 1, 1),
         (311, 1, 1),
         (312, 1, 1),
         (3100, 1, 1),
         (3113, 2, 0),
         (9990, 1, 1),
         (9990, 2, 1),
         (31131, 1, 0),
     ], },
    # 311343 444.050 W4KIP
    {'peer_id': '311343', 'call': 'W4KIP', 'input': '449.050', 'output': '444.050', 'color_code': '1',
     'location': 'Pine Log Mountain, Waleska, GA', 'network': 'Brandmeister',
     'notes': 'Any Brandmeister talk group may be activated on Time Slot 1',
     'talk_groups': [
         (2, 2, 0),
         (9, 2, 0),
         (91, 1, 1),
         (93, 1, 1),
         (310, 1, 1),
         (311, 1, 1),
         (312, 1, 1),
         (3100, 1, 1),
         (3113, 2, 0),
         (9990, 1, 1),
         (9990, 2, 1),
         (31131, 1, 0),
     ], },
    # 311350 444.050 KM4DND Waycross
    {'peer_id': '311350', 'call': 'KM4DND', 'input': '449.025', 'output': '444.025', 'color_code': '3',
     'location': 'Waycross, GA', 'network': 'DMR-SE',
     'notes': '',
     'talk_groups': [
         (1, 1, 0),
         (2, 2, 0),
         (3, 1, 0),
         (9, 1, 0),
         (13, 1, 1),
         (3112, 1, 1),
         (3113, 1, 0),
         (3174, 1, 0),
         (310592, 2, 0),
     ], },
    # TODO 311617 KE4PMP Parrot GA
    # 311637 NG4RF sawnee/cumming
    {'peer_id': '311637', 'call': 'NG4RF', 'input': '447.1125', 'output': '442.1125', 'color_code': '1',
     'location': 'Sawnee Mountain GA', 'network': 'K4USD',
     'talk_groups': [
         (1, 1, 1),
         (2, 2, 0),
         (3, 1, 1),
         (8, 1, 0),
         (9, 2, 0),
         (10, 1, 1),
         (13, 1, 1),
         (91, 1, 1),
         (93, 1, 1),
         (133, 1, 1),
         (310, 2, 1),
         (311, 2, 1),
         (312, 2, 1),
         (313, 2, 1),
         (314, 2, 1),
         (315, 2, 1),
         (316, 2, 1),
         (317, 2, 1),
         (318, 2, 1),
         (319, 2, 1),
         (1776, 2, 1),
         (3100, 2, 1),
         (3112, 2, 1),
         (3113, 2, 0),
         (3121, 2, 1),
         (3125, 2, 1),
         (3127, 2, 1),
         (3133, 2, 1),
         (3139, 2, 1),
         (3145, 2, 1),
         (3147, 2, 1),
         (3148, 2, 1),
         (3155, 2, 1),
         (3172, 2, 1),
         (3174, 2, 1),
         (3175, 2, 1),
         (3176, 2, 1),
         (3182, 2, 1),
         (8951, 2, 1),
         (9998, 2, 1),
         (31012, 2, 1),
         (31121, 2, 1),
         (31130, 2, 1),
         (31134, 2, 1),
         (31139, 2, 1),
         (31665, 2, 1),
         (314710, 2, 1),
     ], },
    # 312243 442.2375 WA4OKJ Rome
    {'peer_id': '312243', 'call': 'WA4OKJ', 'input': '447.2375', 'output': '442.2375', 'color_code': '1',
     'location': 'Mt. Alto Rome GA', 'network': 'Brandmeister',
     'talk_groups': [
         (91, 1, 1),
         (93, 1, 1),
         (312, 2, 1),
         (3100, 2, 1),
         (3112, 2, 1),
         (3113, 2, 0),
         (3124, 2, 1),
         (3137, 2, 1),
         (3147, 2, 1),
         (3155, 2, 1),
         (31121, 2, 1),
         (31131, 2, 1),
         (31665, 2, 1),
     ], },
    # 312284 442.2375 KD4IEZ Dublin
    {'peer_id': '312284', 'call': 'KD4IEZ', 'input': '449.7875', 'output': '444.7875', 'color_code': '1',
     'location': 'Dublin GA', 'network': 'DMR-SE',
     'talk_groups': [
         (1, 1, 1),
         (3113, 2, 0),
         (31131, 2, 1),
         (310592, 2, 0),
     ], },
    # TODO 312391 KE4PMP Cochran GA
    # 312444  KZ4FOZ Athens
    {'peer_id': '312444', 'call': 'KZ4FOX', 'input': '445.6625', 'output': '440.6625', 'color_code': '5',
     'location': 'Athens GA', 'network': 'Brandmeister',
     'notes': 'This is a full-time DMR repeater connected to the BrandMeister network. Both time slots can access any talk group connected to that network.',
     'talk_groups': [
         (8, 1, 1),
         (91, 1, 1),
         (3100, 2, 0),
         (3113, 2, 0),
         (31131, 2, 1),
     ], },
    # 312477 WX4EMA Macon GA K4USD
    {'peer_id': '312477', 'call': 'WX4EMA', 'input': '448.075', 'output': '443.075', 'color_code': '7',
     'location': 'Macon GA', 'network': 'Brandmeister',
     'notes': '',
     'talk_groups': [
         (3113, 2, 0),
         (31135, 1, 0),
     ], },
    # 312477 WXYEMA Macon GA K4USD
    {'peer_id': '312779', 'call': 'WY4EMA', 'input': '445.575', 'output': '440.575', 'color_code': '1',
     'location': 'Macon GA', 'network': 'Brandmeister',
     'notes': '',
     'talk_groups': [
         (3113, 2, 0),
         (31135, 1, 0),
     ], },
]

talk_group_name_to_number_mapping = {}
talk_group_number_to_data_mapping = {}

for network in networks:
    talk_group_name_to_number_mapping[network] = {}
    talk_group_number_to_data_mapping[network] = {}
    for talk_group in talk_groups[network]:
        talk_group_name_to_number_mapping[network][talk_group['name']] = talk_group
        talk_group_number_to_data_mapping[network][talk_group['tg']] = talk_group
