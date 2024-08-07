from libqtile import hook
from libqtile.widget import base
from libqtile.log_utils import logger
from libqtile.core.manager import Qtile
from subprocess import Popen, PIPE
import typing
import asyncio

class KeyboardLayoutAsync(base._TextBox):
    """
    Display keyboard layout the moment it changes!
    Depends upon xkblayout-state and xkblayout-subscribe so be sure to install it!


    """
    defaults = [
        ("xkblayout_state_bin", "xkblayout-state", "path to the xkblayout-state binary, provide it when binary not in PATH"),
        ("xkblayout_subscribe_bin", "xkblayout-subscribe", "path to the xkblayout-subscribe binary, provide it when binary not in PATH"),
        ("display_map", None,
        "Custom display of layout. Key should be in format "
            "of short strings depicting layout. For example: "
            "{'us': 'us', 'lt sgs': 'sgs', 'ru phonetic': 'ru'}" ),
    ]  # type: list[tuple[str, typing.Any, str]]

    keyboard_layouts:list[str] = []

    qtile: Qtile
    _process_sub: Popen | None = None
    future:asyncio.Future

    def __init__(self, **config):
        super().__init__("□", **config)
        self.add_defaults(KeyboardLayoutAsync.defaults)
        self.update_interval = None
    
    def poll(self):
        if self._process_sub is None:
            self._process_sub = Popen(self.xkblayout_subscribe_bin, shell=True, stdout=asyncio.subprocess.PIPE)
        
        if self._process_sub.returncode is not None:
            self._process_sub.communicate()
            self._process_sub.wait()
            del self._process_sub
            self._process_sub = Popen(self.xkblayout_subscribe_bin, shell=True, stdout=asyncio.subprocess.PIPE)
        
        if self._process_sub.stdout is None: return
        
        state = (self._process_sub.stdout.readline()).decode().strip()
        if state == '':
            _ = self._process_sub.wait()
            return
        else:
            state = int(state)
        return self.display_map.get(self.keyboard_layouts[state],self.keyboard_layouts[state])
    
    def update_available_keyboard_layouts(self,xkblayout_state_bin:str|None=None):
        p = Popen(f"{self.xkblayout_state_bin} print %S", stdout=asyncio.subprocess.PIPE, shell=True)
        p.wait()
        self.keyboard_layouts = p.communicate()[0].decode().strip().split("\n")
    
    def get_current_layout_state(self,xkblayout_state_bin:str|None=None):
        p = Popen(f"{self.xkblayout_state_bin} print %c", stdout=asyncio.subprocess.PIPE, shell=True)
        p.wait()
        current_state = int(p.communicate()[0].decode().strip())
        self.update(self.display_map.get(self.keyboard_layouts[current_state],self.keyboard_layouts[current_state]))
    
    def timer_setup(self):
        
        def on_done(future:asyncio.Future):
            try:
                logger.debug(f"{future=} {type(future)=}")
                
                result = future.result()
            except Exception:
                result = None
                logger.exception("keyboard poll() raised exceptions, not rescheduling")

            if result is not None:
                try:
                    logger.debug(f"{result=} {type(result)=}")
                    self.update(result)
                    if self.update_interval is not None:
                        self.timeout_add(self.update_interval, self.timer_setup)
                    else:
                        self.timer_setup()
                except Exception:
                    logger.exception("Failed to reschedule keyboard layout")
        self.future = self.qtile.run_in_executor(self.poll)
        self.future.add_done_callback(on_done)

    def _configure(self, qtile:Qtile, bar):
        super()._configure(qtile, bar)
        self.update_available_keyboard_layouts()
        self.get_current_layout_state()
        
        self._setup_hooks()

    
    def _on_restart(self,):
        if not self.future.done():
            self.future.cancel()
        if self._process_sub is None: return
        self._process_sub.kill()
        

    def _setup_hooks(self):
        hook.subscribe.restart(self._on_restart)
    
    # async def _read_from_generator(self):
    #     async for text in async_keyboard_layout.layout_status(self.xkblayout_state_bin,self.xkblayout_subscribe_bin,self.display_map):
    #         self.update(text)
    
    # async def _config_async(self):
    #     await self._read_from_generator()

