#!/bin/bash
cd /home/jeff/cbridge-listener || exit 13
#./reporter.py
./bm_reporter.py
cp ./*.html /home/www/n1kdo/dmr_data
cp ./*.csv /home/www/n1kdo/dmr_data
cp ./*.png /home/www/n1kdo/dmr_data
