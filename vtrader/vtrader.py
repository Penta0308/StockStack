import asyncio

import aiohttp

from stockstack.settings import Settings


class VTRADERS:
    n: int = 0

    @staticmethod
    def namecomposer(n):
        return f"TraderVirtual{n}"


async def init(n: int):
    VTRADERS.n = n
    for i in range(n):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f'http://stockstackfe:{Settings.get()["stockstackfe"]["web"]["port"]}/company',
                    data=(
                            f"""{{"name": "{VTRADERS.namecomposer(i)}", "worktype": null}}"""
                    ).encode(encoding="UTF-8"),
            ) as resp:
                if resp.status not in (201, 409):  # Created, Conflict
                    resp.raise_for_status()


async def tick(i: int, d: int):
    await asyncio.gather(*[_tick(n, i, d) for n in range(VTRADERS.n)])


async def _tick(n: int, i: int, d: int):
    pass
