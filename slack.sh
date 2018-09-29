#!/bin/bash

if [[ -z "$SLACK_RAJCATA" ]]; then
    exit 0
fi

payload="{'text': '$1', 'channel': '#rajcata'}"
curl -s -X POST --data-urlencode payload="$payload" "$SLACK_RAJCATA" &> /dev/null &
