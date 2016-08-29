#using async to maintain a constant session, 
# while placing repeated orders and with occasional optional sleeps
# really freaking fast

import aiohttp
import asyncio
import websockets
import json


class ClientSesh(object):
    def __init__(self):
        self.session = aiohttp.ClientSession()


    async def heartbeat(self, headers):
        hb_url = "https://api.stockfighter.io/ob/api/heartbeat"
        async with self.session as session:
            while True:
                async with session.get(hb_url, headers=headers) as resp:
                    print("heartbeat", resp.status, await resp.text())
                await asyncio.sleep(5)


    async def block_order(self, account, price, quantity, buy_sell, api_key, venue, stock, order_type="limit"):
        order = json.dumps({"orderType":order_type, 
                "qty":quantity, 
                "direction":buy_sell, 
                "account":account, 
                "price":int(price), 
                "stock":stock,
                "venue":venue
                })
        order_url = "https://api.stockfighter.io/ob/api/venues/%s/stocks/%s/orders" % (venue, stock)
        async with self.session as session:
            while True:
                async with session.post(order_url, data=order, headers=api_key) as resp:
                    print("block order", await resp.json())
                # await asyncio.sleep(5)


def main():
    account = "ACCOUNT#HERE"
    venue = "TESTEX"
    api_key = {"X-Starfighter-Authorization":"KEY HERE"}
    stock = "FOO"
    sesh = ClientSesh()
    loop = asyncio.get_event_loop()
    tasks = [
        loop.create_task(sesh.heartbeat(api_key)),
        loop.create_task(sesh.block_order(account, 1500, 10, "buy", api_key, venue, stock, "market")),
        loop.create_task(sesh.block_order(account, 1500, 10, "sell", api_key, venue, stock, "market"))
    ]
    loop.run_until_complete(asyncio.gather(*tasks))


if __name__ == '__main__':
    main()




