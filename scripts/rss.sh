#!/bin/bash

function readrss() {
	rsstail -1 -N -l -u "$1"
}

function dofeed() {
	arg1="$1"
	case "$arg1" in
	hn)
		readrss "https://hnrss.org/frontpage"
		;;
	matrix)
		readrss "https://matrix.org/blog/feed/"
		;;
	ctf)
		readrss "https://ctftime.org/event/list/upcoming/rss/"
		;;
	*)
		echo "This feed is not configured on server."
		;;
	esac
}

if [ "$#" == "0" ]; then
	echo -n "Currently supported feeds are: "
	echo "hn, matrix, ctf"
	exit 0
fi

dofeed $1

exit 0

# EOF
