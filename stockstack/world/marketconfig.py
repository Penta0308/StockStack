from typing import Callable

import psycopg


class MarketConfig:
    @staticmethod
    async def read(
            curfactory: Callable[[], psycopg.AsyncCursor], key: str) -> str:
        async with curfactory() as cur:
            await cur.execute(
                """SELECT value from world.config WHERE key = %s""", (key,), prepare=True
            )
            return (await cur.fetchone())[0]

    @staticmethod
    async def write(
            curfactory: Callable[[], psycopg.AsyncCursor], key: str, value: str, update: bool = True) -> None:
        async with curfactory() as cur:
            if update:
                await cur.execute(
                    """INSERT INTO world.config (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET (key, value) = (excluded.key, excluded.value)""",
                    (key, value),
                    prepare=True,
                )
            else:
                await cur.execute(
                    """INSERT INTO world.config (key, value) VALUES (%s, %s)""",
                    (key, value),
                    prepare=True,
                )
