#!/bin/bash

# w3m must be installed
type w3m >/dev/null 2>&1 || {
	echo "This script requires that you install the packge \"w3m\" on the server."
	exit 0
}

if [ "$#" == "0" ]; then
	echo "You must be browsing some URL. Try \"web news.ycombinator.com\"."
	exit 0
fi

case $1 in
    ''|*[!0-9]*) w3m -dump "$1" ;;
    *) echo "Not a valid URL" ;;
esac

# EOF
