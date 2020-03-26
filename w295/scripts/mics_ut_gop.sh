#!/bin/bash

while true
do
  mysql -u w295 -pasdASD123 -h w295ft.ckge4y2pabwj.us-east-1.rds.amazonaws.com -D w295 < $1
  sleep 1
done
