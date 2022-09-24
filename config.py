# Copyright (c) 2010, 2014 dequis
# Copyright (c) 2010 Aldo Cortesi
# Copyright (c) 2012 Randall Ma
# Copyright (c) 2012-2014 Tycho Andersen
# Copyright (c) 2012 Craig Barnes
# Copyright (c) 2013 horsik
# Copyright (c) 2013 Tao Sauvage
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import subprocess
from pathlib import Path
import sys
from textwrap import shorten
from typing import List  # noqa: F401

from libqtile.command.client import InteractiveCommandClient
from libqtile import bar, hook, layout, qtile, widget
from libqtile.backend import base
from libqtile.config import Click, Drag, Group, Key, Match, Screen
from libqtile.core.manager import Qtile
from libqtile.lazy import lazy
from libqtile.utils import guess_terminal
from libqtile.log_utils import logger
from libqtile.backend.base import Window

WORKING_PATH = Path(__file__).expanduser().absolute().parent

list_always_in_sight = [
    {
        "name": "Picture-in-Picture",
        "wm_class": ["Toolkit", "firefox"],
        "set_opacity": 0.85
    }
]


@lazy.function
def bar_toggle_visibility(qtile:Qtile):
    qtile.cmd_hide_show_bar()
    qtile.cmd_reconfigure_screens() #hack so bar would look somewhat correctly
    # qtile.cmd_next_layout()
    # qtile.cmd_prev_layout()


def is_window_in_list(window:dict):
    name = window.get("name")
    wm_class:list[str] = window.get("wm_class") #type: ignore
    w_id = window.get('id')
    def _filter(_dict: dict):
        comp_name = _dict.get("name", "")
        comp_class = _dict.get("wm_class", [])
        return name == comp_name and wm_class == comp_class
    return list(filter(_filter, list_always_in_sight))


@hook.subscribe.startup_once
def autostart():
    # from subprocess import Popen

    output = Path("/dev/null")
    autostart_file_path = WORKING_PATH / "autostart"
    if autostart_file_path.is_file():
        with output.open("w") as output:
            subprocess.Popen([autostart_file_path], stdout=output, stderr=output)



@hook.subscribe.focus_change
def windows_always_in_sight():
    if qtile is None:
        return
    _qtile: Qtile = qtile
    current_group = _qtile.current_group
    floating_windows_out_of_place = list([ w for w in _qtile.cmd_windows() if w.get("floating", False) and w.get("group") != current_group.name])
    for window in floating_windows_out_of_place:
        w_id = window.get('id')
        if match := is_window_in_list(window):
            _qtile.windows_map[w_id].togroup(current_group.name)
            if opacity:=match[0].get("set_opacity"):
                _qtile.windows_map[w_id].cmd_opacity(opacity)


@hook.subscribe.focus_change
def float_always_on_top(_window:Window=None):
    if qtile is None:
        return
    _qtile: Qtile = qtile
    for window in _qtile.current_group.windows:
        window:Window = window #type: ignore
        if window.floating:
            window.cmd_bring_to_front()
            if window.opacity == 1.0 and not window.fullscreen:
                window.cmd_opacity(float_opacity)
            if window.fullscreen:
                window.cmd_opacity(1)


mod = "mod4"
terminal = guess_terminal()

keys = [
    # Switch between windows
    Key([mod], "h", lazy.layout.left(), desc="Move focus to left"),
    Key([mod], "l", lazy.layout.right(), desc="Move focus to right"),
    Key([mod], "j", lazy.layout.down(), desc="Move focus down"),
    Key([mod], "k", lazy.layout.up(), desc="Move focus up"),
    Key([mod], "space", lazy.layout.next(),
        desc="Move window focus to other window"),

    # Move windows between left/right columns or move up/down in current stack.
    # Moving out of range in Columns layout will create new column.
    Key([mod, "shift"], "h", lazy.layout.shuffle_left(),
        desc="Move window to the left"),
    Key([mod, "shift"], "l", lazy.layout.shuffle_right(),
        desc="Move window to the right"),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down(),
        desc="Move window down"),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up(), desc="Move window up"),

    # Grow windows. If current window is on the edge of screen and direction
    # will be to screen edge - window would shrink.
    Key([mod, "control"], "h", lazy.layout.grow_left(),
        desc="Grow window to the left"),
    Key([mod, "control"], "l", lazy.layout.grow_right(),
        desc="Grow window to the right"),
    Key([mod, "control"], "j", lazy.layout.grow_down(),
        desc="Grow window down"),
    Key([mod, "control"], "k", lazy.layout.grow_up(), desc="Grow window up"),
    Key([mod], "n", lazy.layout.normalize(), desc="Reset all window sizes"),

    # Toggle between split and unsplit sides of stack.
    # Split = all windows displayed
    # Unsplit = 1 window displayed, like Max layout, but still with
    # multiple stack panes
    Key([mod, "shift"], "Return", lazy.layout.toggle_split(),
        desc="Toggle between split and unsplit sides of stack"),
    Key([mod], "Return", lazy.spawn(terminal), desc="Launch terminal"),

    # Toggle between different layouts as defined below
    Key([mod], "Tab", lazy.next_layout(), desc="Toggle between layouts"),
    Key([mod], "w", lazy.window.kill(), desc="Kill focused window"),

    Key([mod, "control"], "r", lazy.restart(), desc="Restart Qtile"),
    Key([mod, "control"], "q", lazy.shutdown(), desc="Shutdown Qtile"),
    Key([mod], "r", lazy.spawncmd(),
        desc="Spawn a command using a prompt widget"),


    Key([mod, "shift"], "r", lazy.spawn("rofi -show drun -modi drun"),
        desc="launch rofi"),
    Key([], 'Print', lazy.spawn("flameshot gui"), desc="make screenshot"),
    Key([mod,], "m", lazy.spawn('sflock -b "[o-o]" -c "#"'), desc="lock the screen"),
    
    Key([mod, "shift"], "f", lazy.window.toggle_fullscreen(), desc="toggle fullscreen for focused window"),
    Key([mod], "f", bar_toggle_visibility(), desc="toggle bar's visibility"),
    
    Key([mod], "s", lazy.widget["mpris2"].play_pause(), desc="play/pause media"),
    Key([mod], "d", lazy.widget["mpris2"].next(), desc="next media"),
    Key([mod], "a", lazy.widget["mpris2"].previous(), desc="previous media"),
]


groups = [Group(i) for i in "12345"]

for i in groups:
    keys.extend([
        # mod1 + letter of group = switch to group
        Key([mod], i.name, lazy.group[i.name].toscreen(toggle=False),
            desc="Switch to group {}".format(i.name)),

        # mod1 + shift + letter of group = switch to & move focused window to group
        Key([mod, "shift"], i.name, lazy.window.togroup(i.name, switch_group=True),
            desc="Switch to & move focused window to group {}".format(i.name)),
        # Or, use below if you prefer not to switch to that group.
        # # mod1 + shift + letter of group = move focused window to group
        # Key([mod, "shift"], i.name, lazy.window.togroup(i.name),
        #     desc="move focused window to group {}".format(i.name)),
    ])

layouts = [
    layout.Columns(border_focus_stack='#d75f5f', margin=2),
    layout.Max(),
    # Try more layouts by unleashing below layouts.
    # layout.Stack(num_stacks=2),
    # layout.Bsp(),
    # layout.Matrix(),
    # layout.MonadTall(),
    # layout.MonadWide(),
    # layout.RatioTile(margin=0),
    layout.Tile(),
    # layout.TreeTab(),
    # layout.VerticalTile(),
    # layout.Zoomy(),
]


widget_defaults = dict(
    background="#302929",
    font='sans',
    fontsize=12,
    padding=3,
)
extension_defaults = widget_defaults.copy()

def tasklist_shortener(text:str):
    chop_list = {
        " Mozilla Firefox": "Firefox",
        "- Chromium": "Chromium",
        "- VSCodium": "VSCodium",
    }
    for identifier in chop_list.keys():
        if identifier in text:
            return chop_list[identifier]
    return shorten(text, 30, placeholder="...")
    # return text

def current_keyboard_layout():
    layouts = {"ru":"🇷🇺", "us":"🇺🇸"}
    p = subprocess.Popen(['xkblayout-state', 'print', '%s'], text=True, stdout=subprocess.PIPE)
    return layouts.get(p.communicate()[0], "unknown layout")

screens = [
    Screen(
        bottom=bar.Bar(
            [
                widget.CurrentLayoutIcon(scale=0.69), # noice
                widget.GroupBox(disable_drag=True),
                widget.Prompt(),
                # widget.WindowName(),
                # widget.TaskList(
                #     rounded=True,
                #     highlight_method="block",
                #     markup_normal='<span alpha="30%">{}</span>',
                #     markup_focused="{}",
                #     markup_minimized="<u>{}</u>",
                #     markup_maximized="<b>{}</b>",
                #     markup_floating="<i>{}</i>",
                #     txt_floating="",
                #     txt_maximized="",
                #     txt_minimized="",
                #     max_chars=3,
                #     padding_y=2,
                #     icon_size=17,
                #     parse_text=tasklist_shortener,
                # ),
                widget.Mpris2(
                    display_metadata=['xesam:artist', 'xesam:title', 'xesam:album'],
                    paused_text="⏸ | {track} |",
                    playing_text="▸ | {track} |",
                    scroll_chars=10,
                ),
                widget.Spacer(),
                widget.CPU(),
                widget.Memory(
                    format="Memory: {MemPercent:.2f}%"
                ),
                widget.Systray(),
                widget.GenPollText(
                    func=current_keyboard_layout,
                    fontsize=20,
                    update_interval=0.5
                ),
                widget.PulseVolume(),
                widget.Clock(
                    format='%H:%M\n<span size="x-small">%d-%m-%Y %a</span>',
                    ),
                widget.QuickExit(),
            ],
            27,
            background=["#302929"],
            opacity=0.9
        ),
    wallpaper=str(WORKING_PATH / "untitled.png"),
    wallpaper_mode="stretch"
    ),
]

# Drag floating layouts.
mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(),
         start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(),
        start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
    Click([mod, "shift"], "Button1", lazy.window.toggle_floating())
]


# Telegram group

import os

groups.append(
    Group("T", matches=[Match(wm_class=["Telegram", "TelegramDesktop"])],
         spawn=os.environ.get("TELEGRAM_EXEC",'echo "oops"'))
)

keys.extend([
    Key([mod], "t", lazy.group['T'].toscreen(toggle=False),
        desc="Switch to group {}".format("T")),
    Key([mod, "shift"], 't', lazy.window.togroup("T", switch_group=True),
        desc="Switch to & move focused window to group {}".format("T")),
])

float_opacity = 0.9
dgroups_key_binder = None
dgroups_app_rules = []  # type: List
follow_mouse_focus = True
bring_front_click = False
cursor_warp = False
floating_layout = layout.Floating(float_rules=[
    # Run the utility of `xprop` to see the wm class and name of an X client.
    *layout.Floating.default_float_rules,
    Match(wm_class='confirmreset'),  # gitk
    Match(wm_class='makebranch'),  # gitk
    Match(wm_class='maketag'),  # gitk
    Match(wm_class='ssh-askpass'),  # ssh-askpass
    Match(title='branchdialog'),  # gitk
    Match(title='pinentry'),  # GPG key password entry
])
auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = True

# If things like steam games want to auto-minimize themselves when losing
# focus, should we respect this or not?
auto_minimize = False

# XXX: Gasp! We're lying here. In fact, nobody really uses or cares about this
# string besides java UI toolkits; you can see several discussions on the
# mailing lists, GitHub issues, and other WM documentation that suggest setting
# this string if your java app doesn't work correctly. We may as well just lie
# and say that we're a working one by default.
#
# We choose LG3D to maximize irony: it is a 3D non-reparenting WM written in
# java that happens to be on java's whitelist.
wmname = "LG3D"

# wmname = "Qtile"
