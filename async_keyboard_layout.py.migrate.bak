import asyncio

async def await_and_print(c):
    print(await c)

async def for_and_print(c):
    async for i in c:
        print(i)

async def get_current_keyboard_state(xkblayout_state_bin:str|None=None) -> int:
    if xkblayout_state_bin is None:
        xkblayout_state_bin = "xkblayout-state"
    p = await asyncio.create_subprocess_shell(f"{xkblayout_state_bin} print %c", stdout=asyncio.subprocess.PIPE)
    await p.wait()
    return int((await p.communicate())[0].decode().strip())
    

async def available_keyboard_layouts(xkblayout_state_bin:str|None=None) -> list[str]:
    if xkblayout_state_bin is None:
        xkblayout_state_bin = "xkblayout-state"
    p = await asyncio.create_subprocess_shell(f"{xkblayout_state_bin} print %S", stdout=asyncio.subprocess.PIPE)
    await p.wait()
    return (await p.communicate())[0].decode().strip().split("\n")

async def layout_status(xkblayout_state_bin:str|None=None, xkblayout_sub_bin:str|None=None, layouts_display={"ru":"🇷🇺", "us":"🇺🇸"}):
    if xkblayout_sub_bin is None:
        xkblayout_sub_bin = "xkblayout-subscribe"
    keyboard_layouts = await available_keyboard_layouts(xkblayout_state_bin)
    state = await get_current_keyboard_state(xkblayout_state_bin)
    yield layouts_display.get(keyboard_layouts[state],keyboard_layouts[state])
    p = await asyncio.create_subprocess_exec(xkblayout_sub_bin, stdout=asyncio.subprocess.PIPE)
    while True:
        if p.returncode is not None:
            await p.communicate()
            await p.wait()
            del p
            p = await asyncio.create_subprocess_exec(xkblayout_sub_bin, stdout=asyncio.subprocess.PIPE)

        if p.stdout is None: continue

        state = (await p.stdout.readline()).decode().strip()
        if state == '' or p.stdout.at_eof():
            _ = await p.wait() 
            continue
        else:
            state = int(state)
        yield layouts_display.get(keyboard_layouts[state],keyboard_layouts[state])


if __name__ == "__main__":
    asyncio.run(await_and_print(available_keyboard_layouts()))
    asyncio.run(await_and_print(get_current_keyboard_state()))
    asyncio.run(for_and_print(layout_status()))

# async def current_keyboard_layout():
#     layouts = {"ru":"🇷🇺", "us":"🇺🇸"}
#     p = subprocess.Popen(['xkblayout-state', 'print', '%s'], text=True, stdout=subprocess.PIPE)
#     return layouts.get(p.communicate()[0], "unknown layout")
