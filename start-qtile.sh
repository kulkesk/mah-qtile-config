sleep 5 &&
killall kwin_x11 &&
qtile start &&
kwin_x11 & disown;