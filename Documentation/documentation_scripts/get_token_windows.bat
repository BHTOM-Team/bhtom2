@ECHO OFF

echo This script will query BHTOM API (http://bhtom.space)
echo for your private security TOKEN. Please follow instructions.

set /p username="Username: "
set /p password="Password: "

echo Querying BHTOM API...

curl -X "POST" -H "accept: application/json" -H "Content-Type: application/json" -H "X-CSRFToken: uUz2fRnXhPuvD9YuuiDW9cD1LsajeaQnE4hwtEAfR00SgV9bD5HCe5i8n4m4KcOr" -d "{\"username\": \"%username%\",\"password\": \"%password%\"}" "https://bh-tom2.astrolabs.pl/api/token-auth/"