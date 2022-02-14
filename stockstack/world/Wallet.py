import aiohttp

from stockstack.settings import Settings


async def putmoney(cid: int, amount: int | None = None):
    async with aiohttp.ClientSession() as session:
        async with session.put(f'http://stockwallet:{Settings.get()["stockwallet"]["web"]["port"]}/wallet/{cid}',
                               data=
                               ('{"user_id": ' + str(cid) + (
                                       f', "amount": {amount}' if amount is not None else '') + '}')
                                       .encode(encoding='UTF-8')) as resp:
            j = await resp.json()
            return j['amount']


async def deltamoney(cid: int, amount: int):
    async with aiohttp.ClientSession() as session:
        async with session.post(f'http://stockwallet:{Settings.get()["stockwallet"]["web"]["port"]}/wallet/{cid}',
                                data=f'{{"amount": {amount} }}'.encode(encoding='UTF-8')) as resp:
            j = await resp.json()
            return j['amount']


async def getmoney(cid: int):
    async with aiohttp.ClientSession() as session:
        async with session.get(
                f'http://stockwallet:{Settings.get()["stockwallet"]["web"]["port"]}/wallet/{cid}') as resp:
            j = await resp.json()
            return j['amount']