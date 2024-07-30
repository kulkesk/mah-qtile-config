from libqtile import hook
from libqtile.widget import base
from libqtile.log_utils import logger
from libqtile.core.manager import Qtile
import importlib

import asyncio
import concurrent.futures
from typing import Callable, Any
from multiprocessing import Process, Value

# from xkblayout_module_wrapper import update as layout_update

def ignore_exceptions(func:Callable):
    def wrapper(*arg, **kwarg):
        logger.warn(f"TRIGGERED {func}")
        try:
            return func()
        except Exception as err:
            logger.warn(f"{func} is faulted, with error {err}")
            return
    return wrapper


def get_update(num):
    # print(f"entered `get_update`")
    xkbls = importlib.import_module("xkblayout_subscribe")
    xkbls.init()
    while True:
        value = xkbls.update()
        with num.get_lock():
            # print(f"value is: {value}")
            num.value=value
            # print("set the value")
    xkbls.deinit()
    # print("exit")


class KeyboardLayoutAsync(base.ThreadPoolText):
    defaults = [
        ("xkblayout_state_bin", "xkblayout-state", "path to the xkblayout-state binary, provide it when binary not in PATH"),
        ("display_map", None,
        "Custom display of layout. Key should be in format "
            "of short strings depicting layout. For example: "
            "{'us': 'us', 'lt sgs': 'sgs', 'ru phonetic': 'ru'}" )
    ]
    keyboard_layouts:list[str] = []

    qtile: Qtile
    future:asyncio.Future
    process:Process|None = None
    num = None
    

    def __init__(self, **config):
        super().__init__("□", **config)
        logger.warn(f"{type(self).__name__} Initinalized!")
        self.add_defaults(KeyboardLayoutAsync.defaults)
        self.update_interval = 0

    def update_available_keyboard_layouts(self,xkblayout_state_bin:str|None=None):
        self.keyboard_layouts = self.call_process(f"{self.xkblayout_state_bin} print %S", shell=True).strip().split("\n")
    
    def get_current_layout_state(self,xkblayout_state_bin:str|None=None):
        current_state = int(self.call_process(f"{self.xkblayout_state_bin} print %c", shell=True).strip())
        self.update(self.display_map.get(self.keyboard_layouts[current_state], self.keyboard_layouts[current_state]))

    
    def poll(self):
        # loop = asyncio.get_running_loop()
        # with councurrent.futures.ProcessPoolExecutor() as pool:

        if not self.num and not self.process:
            self.num = Value("I", 0)
            self.process = Process(target=get_update, args=(self.num,))
            self.process.start()

        with self.num.get_lock():
            updated_value = int(self.num.value)

        try:
            new_state = self.keyboard_layouts[updated_value]
        except IndexError:
            logger.info(f"Index error! Updating available keyboard layouts! right now they are: {self.keyboard_layouts = }")
            self.update_available_keyboard_layouts()
            logger.info(f"Updated keyboard layouts! {self.keyboard_layouts = }")
            new_state = self.keyboard_layouts[updated_value]
        return self.display_map.get(new_state, new_state)
    
    # def init_xkbls(self):
    #     if xkbls.init():
    #         raise RuntimeError("couldn't run the `init` function for `xkbls`")
    
    def process_kill(self):
        if self.process:
            self.process.kill()
    
    def _setup_hooks(self):
        pass
        # hook.subscribe.startup(self.init_xkbls)
        hook.subscribe.shutdown(self.process_kill)
        hook.subscribe.restart(self.process_kill)


    def _configure(self, qtile:Qtile, bar):
        super()._configure(qtile, bar)
        self.update_available_keyboard_layouts()
        self.get_current_layout_state()
        self._setup_hooks()

