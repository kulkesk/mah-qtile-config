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
import os
from textwrap import shorten
from typing import List, Optional, Callable

from libqtile.command.client import InteractiveCommandClient
from libqtile import bar, hook, layout, qtile, widget
from libqtile.backend import base
from libqtile.config import Click, Drag, Group, Key, Match, Screen
from libqtile.core.manager import Qtile
from libqtile.lazy import lazy
from libqtile.utils import guess_terminal
from libqtile.log_utils import logger
from libqtile.backend.base import Window

from hideble_bar import HidebleGap

WORKING_PATH = Path(__file__).expanduser().absolute().parent

list_always_in_sight = [
    {
        "name": "Picture-in-Picture",
        "wm_class": ["Toolkit", "firefox"],
        "set_opacity": 1,
    },
    {
        "name": "PureRef",
        "wm_class": ["PureRef", "PureRef"],
        "set_opacity": 1,
    }
]

bar_state = 0

@lazy.function
def bar_toggle_visibility(qtile:Qtile):
    global bar_state
    match bar_state:
        case 0:
            qtile.cmd_hide_show_bar("bottom")
        case 1:
            qtile.cmd_hide_show_bar("top")
    
    bar_state = (bar_state + 1) % 2
    

def is_window_in_list(window:Optional[dict|Window]):
    if window is None:
        return
    if isinstance(window,dict):
        name = window.get("name")
        wm_class = window.get("wm_class") #type: ignore
    else:
        name = window.name
        wm_class = window.get_wm_class()

    def _filter(_dict: dict):
        comp_name = _dict.get("name", "")
        comp_class = _dict.get("wm_class", [])
        return name == comp_name or wm_class == comp_class

    return list(filter(_filter, list_always_in_sight))


@hook.subscribe.startup
def dump_PID_into_a_file():
    with (WORKING_PATH / "pid").open("w") as file:
        file.write(str(os.getpid()))


@hook.subscribe.startup_once
def autostart():
    # from subprocess import Popen

    output = Path("/dev/null")
    autostart_file_path = WORKING_PATH / "autostart"
    if autostart_file_path.is_file():
        with output.open("w") as output:
            subprocess.Popen([autostart_file_path], stdout=output, stderr=output)



# @hook.subscribe.focus_change
@hook.subscribe.client_new
def windows_always_in_sight(win:Window|None=None):
    if qtile is None:
        return
    _qtile: Qtile = qtile
    try:
        current_group = _qtile.current_group
    except AttributeError:
        return
    floating_windows_out_of_place = list([ w for w in _qtile.cmd_windows() if w.get("floating", False) and w.get("group") != current_group.name])
    for window in floating_windows_out_of_place:
        w_id = window['id']
        if match := is_window_in_list(window):
            window_obj:Window = _qtile.windows_map[w_id] # type: ignore
            window_obj.togroup(current_group.name)
            current_group.cmd_prev_window()
            if not window_obj.floating:
                window_obj.floating = True
            if opacity:=match[0].get("set_opacity"):
                window_obj.cmd_opacity(opacity)
            del window_obj


@hook.subscribe.client_new
# @hook.subscribe.focus_change
def float_always_on_top(_window:Window|None=None):
    if qtile is None:
        return
    _qtile: Qtile = qtile
    focus_history: list[Window] = _qtile.current_group.focus_history
    if len(focus_history) <= 1:
        return
    if focus_history[-2].floating and focus_history[-1].floating: # fix for continuesly switching floating windows
        return
    # if is_window_in_list(focus_history[-1]) and is_window_in_list(focus_history[-2]):
    #     return
    always_in_sight = list()
    for window in _qtile.current_group.windows:
        window:Window = window #type: ignore
        if window.floating:
            window.cmd_bring_to_front()
            if is_window_in_list(window):
                always_in_sight.append(window)
    for window in always_in_sight:
        window.cmd_bring_to_front()
    

@lazy.function
def always_on_top_lazy(*args):
    float_always_on_top()

@lazy.function
def windows_always_in_sight_lazy(*args):
    windows_always_in_sight()


@hook.subscribe.client_new
# @hook.subscribe.client_focus
def set_windows_static(c:Window):
    if c.name == "Desktop — Plasma":
        qtile = c.qtile
        
        other_windows = [window for window in qtile.windows_map.values() if window.name != "Desktop — Plasma" and hasattr(window, "cmd_bring_to_front")]
        for window in other_windows:
            window.cmd_bring_to_front() # type: ignore
        c.cmd_static(None,0,0,1366,768)
    win_type = c.get_wm_type()
    if win_type is not None:
        if "_NET_WM_WINDOW_TYPE_DOCK," in win_type.split():
            c.cmd_static()
    if wmclass := c.get_wm_class():
        if "plasmashell" in wmclass:
            c.borderwidth = 0
    # c.borderwidth=0


mod = "mod4"
terminal = guess_terminal("alacritty")

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
    # Key([mod,], "m", lazy.spawn('sflock -b "[o-o]" -c "#"'), desc="lock the screen"),
    
    Key([mod, "shift"], "f", lazy.window.toggle_fullscreen(), desc="toggle fullscreen for focused window"),
    Key([mod], "f", bar_toggle_visibility(), desc="toggle bar's visibility"),
    
    # media control
    Key([mod], "s", lazy.widget["mpris2"].play_pause(), desc="play/pause media"),
    Key([mod], "d", lazy.widget["mpris2"].next(), desc="next media"),
    Key([mod], "a", lazy.widget["mpris2"].previous(), desc="previous media"),
    
    # volume control
    Key([mod], "e", lazy.widget["pulsevolume"].increase_vol(5), desc="increase volume"),
    Key([mod], "q", lazy.widget["pulsevolume"].decrease_vol(5), desc="decrease volume"),
    Key([mod, "shift"], "e", lazy.widget["pulsevolume"].increase_vol(1), desc="increase volume by one"),
    Key([mod, "shift"], "q", lazy.widget["pulsevolume"].decrease_vol(1), desc="decrease volume by one"),
    # Key([mod, "shift"], "q", lazy.widget["pulsevolume"].mute(), desc="mute"),
]


groups = [Group(i) for i in "12345"]

for i in groups:
    keys.extend([
        # mod1 + letter of group = switch to group
        Key([mod], i.name, lazy.group[i.name].toscreen(toggle=False), windows_always_in_sight_lazy(),
            desc="Switch to group {}".format(i.name)),

        # mod1 + shift + letter of group = switch to & move focused window to group
        Key([mod, "shift"], i.name, lazy.window.togroup(i.name, switch_group=True), windows_always_in_sight_lazy(),
            desc="Switch to & move focused window to group {}".format(i.name)),
        # Or, use below if you prefer not to switch to that group.
        # # mod1 + shift + letter of group = move focused window to group
        # Key([mod, "shift"], i.name, lazy.window.togroup(i.name),
        #     desc="move focused window to group {}".format(i.name)),
    ])


default_for_layouts=dict(
    margin = 0,
    border_width = 2,
    border_normal = "#11111b",
    border_focus = "#b4befe",
)

layouts = [
    layout.Max(),
    # Try more layouts by unleashing below layouts.
    # layout.Stack(num_stacks=2),
    # layout.Bsp(),
    # layout.Matrix(),
    # layout.MonadTall(),
    # layout.MonadWide(),
    # layout.RatioTile(margin=0),
    layout.Tile(
        add_on_top=False,
        border_on_single=False,
        **default_for_layouts
    ),
    layout.Columns(border_focus_stack='#d75f5f', **default_for_layouts),
    # layout.TreeTab(),
    # layout.VerticalTile(),
    # layout.Zoomy(),
]


widget_defaults = dict(
    background="#181825",
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
        top=HidebleGap(24),
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
                    width=600,
                    display_metadata=['xesam:artist', 'xesam:title', 'xesam:album'],
                    paused_text="⏸ | {track} |",
                    playing_text="    | {track} |",
                    scroll=True,
                    # max_chars=60,
                    scroll_chars=5,
                ),
                widget.Spacer(),
                widget.CPU(
                    format='CPU {freq_current:>03.1f}GHz {load_percent:>04.1f}%'
                ),
                widget.Memory(
                    format="Memory: {MemPercent:>04.1f}%"
                ),
                # widget.Systray(),
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
            background=["#18182530"],
            opacity=1
        ),
    wallpaper=str(WORKING_PATH / "untitled.png"),
    wallpaper_mode="stretch"
    ),
]

# Drag floating layouts.
mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(), always_on_top_lazy(),
         start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(),
        start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
    Click([mod, "shift"], "Button1",lazy.window.toggle_floating(), always_on_top_lazy())
]


# Telegram group

import os

groups.append(
    Group("T", matches=[Match(wm_class=["Telegram", "TelegramDesktop"])],  # type: ignore
         spawn=os.environ.get("TELEGRAM_EXEC",'echo "oops"'))
)

keys.extend([
    Key([mod], "t", lazy.group['T'].toscreen(toggle=False), windows_always_in_sight_lazy(),
        desc="Switch to group {}".format("T")),
    Key([mod, "shift"], 't', lazy.window.togroup("T", switch_group=True), windows_always_in_sight_lazy(),
        desc="Switch to & move focused window to group {}".format("T")),
])

dgroups_key_binder = None
dgroups_app_rules = []  # type: List
follow_mouse_focus = True
bring_front_click = False
cursor_warp = False # _KDE_NET_WM_WINDOW_TYPE_APPLET_POPUP
floating_layout = layout.Floating(float_rules=[
    # Run the utility of `xprop` to see the wm class and name of an X client.
    *layout.Floating.default_float_rules,
    Match(wm_class='confirmreset'),  # gitk
    Match(wm_class='makebranch'),  # gitk
    Match(wm_class='maketag'),  # gitk 
    Match(wm_class='ssh-askpass'),  # ssh-askpass
    Match(wm_class='ibus-ui-emojier-plasma'),  # emoji selector
    Match(title='branchdialog'),  # gitk
    Match(title='pinentry'),  # GPG key password entry
    Match(wm_class="PureRef"),  # PureRef
    Match(wm_class="plasmashell"),  # PureRef
    # _NET_WM_WINDOW_TYPE(ATOM) = _KDE_NET_WM_WINDOW_TYPE_APPLET_POPUP
], **default_for_layouts)
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
