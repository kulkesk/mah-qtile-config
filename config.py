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


import os
import subprocess
import sys
from pathlib import Path
from textwrap import shorten
from typing import Callable, List, Optional

from async_keyboard_widget_cython import KeyboardLayoutAsync
from bindings import keys, mod, terminal
from graphical_notifications import Notifier
# from libqtile.command.client import InteractiveCommandClient
from libqtile import bar, hook, layout, qtile, widget
from libqtile.log_utils import logger
from libqtile.backend.base import Window
# from libqtile.backend import base
from libqtile.config import Click, Drag, Group, Key, Match, Screen
from libqtile.core.manager import Qtile
from libqtile.lazy import lazy
from libqtile.utils import guess_terminal

# from hideble_bar import HidebleGap


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
    },
    {
        "name": "KeePassXC -  Access Request",
        "wm_class": ["keepassxc", "KeePassXC"],
        "set_opacity": 1,
    },
]

if os.environ.get("QTILE_XEPHYR"):
    XEPHYR = True
else:
    XEPHYR = False


def is_window_in_list(window: Optional[dict | Window]):
    if window is None:
        return
    if isinstance(window, dict):
        name = window.get("name")
        wm_class = window.get("wm_class")  # type: ignore
    else:
        name = window.name
        wm_class = window.get_wm_class()

    def _filter(_dict: dict):
        comp_name = _dict.get("name", "")
        comp_class = _dict.get("wm_class", [])
        return name == comp_name or wm_class == comp_class

    return list(filter(_filter, list_always_in_sight))


if not XEPHYR:

    @hook.subscribe.startup_once
    def autostart():
        # from subprocess import Popen

        output = Path("/dev/null")
        autostart_file_path = WORKING_PATH / "autostart"
        if autostart_file_path.is_file():
            with output.open("w") as output:
                subprocess.Popen([autostart_file_path], stdout=output, stderr=output)


# @hook.subscribe.focus_change
# @hook.subscribe.client_new
@hook.subscribe.client_managed
def windows_always_in_sight(win: Window | None = None):
    # return
    if qtile is None:
        return
    _qtile: Qtile = qtile
    try:
        current_group = _qtile.current_group
    except AttributeError:
        return
    floating_windows_out_of_place = list(
        [
            w
            for w in _qtile.windows()
            if w.get("floating", False) and w.get("group") != current_group.name
        ]
    )
    for window in floating_windows_out_of_place:
        w_id = window["id"]
        window_obj: Window = _qtile.windows_map[w_id]  # type: ignore
        if match := is_window_in_list(window):
            window_obj.togroup(current_group.name)
            current_group.prev_window()
            if not window_obj.floating:
                window_obj.floating = True
            if opacity := match[0].get("set_opacity"):
                window_obj.set_opacity(opacity)
            del window_obj
    if win is None:
        return
    # logger.warning(f"{win.name=}")
    if "KeePassXC" in win.name:
        logger.warn("we got in here!")
        win.bring_to_front()
        win.bring_to_front()
        win.bring_to_front()



@hook.subscribe.client_managed
# @hook.subscribe.focus_change
def float_always_on_top(_window: Window | None = None):
    return
    if qtile is None:
        return
    _qtile: Qtile = qtile
    focus_history: list[Window] = _qtile.current_group.focus_history
    if len(focus_history) <= 1:
        return
    if (
        focus_history[-2].floating and focus_history[-1].floating
    ):  # fix for continuesly switching floating windows
        return
    # if is_window_in_list(focus_history[-1]) and is_window_in_list(focus_history[-2]):
    #     return
    always_in_sight = list()
    for window in _qtile.current_group.windows:
        window: Window = window  # type: ignore
        if window.floating:
            window.bring_to_front()
            if is_window_in_list(window):
                always_in_sight.append(window)
    for window in always_in_sight:
        window.bring_to_front()
    if _window is None:
        return
    # logger.warning(f"{_win.name=}")
    if "KeePassXC" in _window.get_wm_class():
        _window.bring_to_front()


@lazy.function
def always_on_top_lazy(*args):
    float_always_on_top()


@lazy.function
def windows_always_in_sight_lazy(*args):
    windows_always_in_sight()


groups = []

groups.extend([Group(i) for i in "12345"])


for i in groups:
    keys.extend(
        [
            # mod1 + letter of group = switch to group
            Key(
                [mod],
                i.name,
                lazy.group[i.name].toscreen(toggle=False),
                windows_always_in_sight_lazy(),
                # always_on_top_lazy(),
                desc="Switch to group {}".format(i.name),
            ),
            # mod1 + shift + letter of group = switch to & move focused window to group
            Key(
                [mod, "shift"],
                i.name,
                lazy.window.togroup(i.name, switch_group=True),
                windows_always_in_sight_lazy(),
                # always_on_top_lazy(),
                desc="Switch to & move focused window to group {}".format(i.name),
            ),
            # Or, use below if you prefer not to switch to that group.
            # # mod1 + shift + letter of group = move focused window to group
            # Key([mod, "shift"], i.name, lazy.window.togroup(i.name),
            #     desc="move focused window to group {}".format(i.name)),
        ]
    )


from libqtile.config import DropDown, ScratchPad

groups.append(
    ScratchPad(
        "scratchpad",
        [
            DropDown(
                "term", "alacritty -e python", on_focus_lost_hide=False, opacity=0.95
            ),  # type:ignore
        ],
    )
)
keys.append(
    Key(
        [mod],
        "F3",
        lazy.group["scratchpad"].dropdown_toggle("term"),
        desc="stuff and then some",
    )
)


default_for_layouts = dict(
    margin=0,
    border_width=2,
    border_normal="#11111b",
    border_focus="#b4befe",
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
    layout.Tile(add_on_top=False, border_on_single=False, **default_for_layouts),
    layout.Columns(border_focus_stack="#d75f5f", **default_for_layouts),
    # layout.TreeTab(),
    # layout.VerticalTile(),
    # layout.Zoomy(),
]


widget_defaults = dict(
    foreground="#cdd6f4",
    background="#181825",
    font="FiraCode Nerd Font Mono",
    fontsize=12,
    padding=3,
)
extension_defaults = widget_defaults.copy()


def tasklist_shortener(text: str):
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


screens = [
    Screen(
        # top=HidebleGap(24),
        bottom=bar.Bar(
            [
                widget.CurrentLayoutIcon(scale=0.69),  # noice
                widget.GroupBox(
                    disable_drag=True,
                    # mouse_callbacks={
                    #     "Button1": [windows_always_in_sight_lazy(),
                    #     "Button4": windows_always_in_sight_lazy(),
                    #     "Button5": windows_always_in_sight_lazy(),
                    # }
                ),
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
                    width=500,
                    # {xesam:title} - {xesam:album} - {xesam:artist}
                    # display_metadata=["xesam:artist", "xesam:title", "xesam:album"],
                    paused_text=" │ {xesam:artist} - {xesam:title} │",
                    playing_text=" │ {xesam:artist} - {xesam:title} │",
                    scroll=True,
                    # max_chars=60,
                    scroll_chars=5,
                ),
                widget.Spacer(),
                widget.Sep(),
                widget.ThermalSensor(
                    padding=0,
                    tag_sensor="Package id 0",
                    format="CPU:{temp:>02.1f}{unit} ",
                    foreground_alert=widget_defaults.get("foreground", "#ffffff"),
                ),
                widget.CPU(
                    # format='{freq_current:>03.1f}GHz {load_percent:>04.1f}%'
                    format="{load_percent:>04.1f}%",
                    padding=0,
                ),
                widget.Sep(),
                widget.ThermalSensor(
                    padding=0,
                    tag_sensor="edge",
                    format="GPU:{temp:>02.1f}{unit}",
                    foreground_alert=widget_defaults.get("foreground", "#ffffff"),
                ),
                widget.Sep(),
                widget.Memory(
                    padding=0,
                    format="RAM: {MemPercent:>04.1f}%│Swap: {SwapPercent:>04.1f}%",
                ),
                widget.Sep(),
                widget.Systray(),
                widget.Sep(),
                widget.PulseVolume(padding=0, fmt="{}"),
                widget.Sep(),
                widget.Clock(
                    padding=10,
                    format='%H:%M\n<span size="small">%d.%m.%Y %a</span>',
                ),
                # widget.QuickExit(),
                # widget.Spacer(length=5)
            ],
            27,
            background=["#1e1e2e"],
            opacity=1,
        ),
        wallpaper=str(WORKING_PATH / "wallpaper.jpg"),
        wallpaper_mode="stretch",
    ),
]
# screens[0].bottom

# Drag floating layouts.
mouse = [
    Drag(
        [mod],
        "Button1",
        lazy.window.set_position_floating(),
        # always_on_top_lazy(),
        start=lazy.window.get_position(),
    ),
    Drag(
        [mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()
    ),
    Click([mod], "Button2", lazy.window.bring_to_front()),
    Click(
        [mod, "shift"], "Button1", lazy.window.toggle_floating(),
        # always_on_top_lazy()
    ),
]


# Telegram group

import os

groups.append(
    Group(
        "T",
        matches=[Match(wm_class=["Telegram", "TelegramDesktop"])],  # type: ignore
        spawn=os.environ.get("TELEGRAM_EXEC", 'echo "oops"'),
    )
)

keys.extend(
    [
        Key(
            [mod],
            "t",
            lazy.group["T"].toscreen(toggle=False),
            windows_always_in_sight_lazy(),
            # always_on_top_lazy(),
            desc="Switch to group {}".format("T"),
        ),
        Key(
            [mod, "shift"],
            "t",
            lazy.window.togroup("T", switch_group=True),
            windows_always_in_sight_lazy(),
            # always_on_top_lazy(),
            desc="Switch to & move focused window to group {}".format("T"),
        ),
    ]
)


# TODO: make height and width set programmatically
HEIGHT = 768
WIDTH = 1366
notifier = Notifier(
    y=10,
    x=WIDTH - 310,
    width=300,
    height=69,
    format="<b>{summary}</b>\n{body}",
    border=("#b4befe",) * 3,
    overflow="more_width",
    border_width=2,
    opacity=0.85,
    **widget_defaults,
)

keys.extend(
    [
        Key([mod], "grave", lazy.function(notifier.prev)),
        Key([mod, "shift"], "grave", lazy.function(notifier.next)),
        Key([mod, "control"], "grave", lazy.function(notifier.close)),
    ]
)

dgroups_key_binder = None
dgroups_app_rules = []  # type: List
follow_mouse_focus = True
bring_front_click = False
floats_kept_above = True
cursor_warp = False  # _KDE_NET_WM_WINDOW_TYPE_APPLET_POPUP
floating_layout = layout.Floating(
    float_rules=[
        # Run the utility of `xprop` to see the wm class and name of an X client.
        *layout.Floating.default_float_rules,
        Match(wm_class="confirmreset"),  # gitk
        Match(wm_class="makebranch"),  # gitk
        Match(wm_class="maketag"),  # gitk
        Match(wm_class="ssh-askpass"),  # ssh-askpass
        Match(wm_class="ibus-ui-emojier-plasma"),  # emoji selector
        Match(title="branchdialog"),  # gitk
        Match(title="pinentry"),  # GPG key password entry
        Match(wm_class="plasmashell"),  # PureRef
        # _NET_WM_WINDOW_TYPE(ATOM) = _KDE_NET_WM_WINDOW_TYPE_APPLET_POPUP
    ],
    **default_for_layouts,
)
auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = True

floats_kept_above = True
bring_front_click = False
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
