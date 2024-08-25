#!/usr/bin/bash
# A="b'[{\"uptime\": \"$(uptime -p)\",\"feelgood\": \"$(ps)\"}]'"

STATUS="b'[{"
additem(){
	STATUS="${STATUS}\"$1\": \"$($2)\","
}

additem uptime uptime
echo $STATUS



