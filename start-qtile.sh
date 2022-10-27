#!/usr/bin/env bash
while true; do
	killall -9 kwin_x11;
	qtile start;
done
# kwin_x11 & disown;
