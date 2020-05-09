#!/bin/bash
cd /home/jeff/cbridge-listener
./reporter.py
cp ./*.html /home/www/n1kdo/dmr_data
cp ./*.csv /home/www/n1kdo/dmr_data
cp ./*.png /home/www/n1kdo/dmr_data
