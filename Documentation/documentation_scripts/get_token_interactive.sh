#!/bin/bash

echo " "
echo " ### This script will query BHTOM API (http://bhtom.space)"
echo " ### for your private security TOKEN. Please follow instructions."
echo " "
echo " "
echo -n " > Username: "; read username
echo -n " > Password: "; read password
echo " "
echo -n " > Querying BHTOM API..."

curl -X 'POST' \
  'https://bh-tom2.astrolabs.pl/api/token-auth/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -H 'X-CSRFToken: uUz2fRnXhPuvD9YuuiDW9cD1LsajeaQnE4hwtEAfR00SgV9bD5HCe5i8n4m4KcOr' \
  -d '{
  "username": "'"${username}"'",
  "password": "'"${password}"'"
}'

echo -e "\n"
exit 0

### BHTOM, ver. of Nov 8, 2023
### END
