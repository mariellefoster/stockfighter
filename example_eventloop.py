import aiohttp
# import asyncio
import asyncio
import websockets
import json


async def heartbeat(headers):
    hb_url = "https://api.stockfighter.io/ob/api/heartbeat"
    async with aiohttp.ClientSession() as session:
        while True:
            async with session.get(hb_url, headers=headers) as resp:
                print("heartbeat", resp.status, await resp.text())
            await asyncio.sleep(5)


async def block_order(account, price, quantity, buy_sell, api_key, venue, stock, order_type="limit"):
    order = json.dumps({"orderType":order_type, 
            "qty":quantity, 
            "direction":buy_sell, 
            "account":account, 
            "price":int(price), 
            "stock":stock,
            "venue":venue
            })
    order_url = "https://api.stockfighter.io/ob/api/venues/%s/stocks/%s/orders" % (venue, stock)
    async with aiohttp.ClientSession() as session:
        async with session.post(order_url, data=order, headers=api_key) as resp:
            print("block order", await resp.json())




async def handle_stockfighter(account, venue, socket_type):

    url = 'wss://api.stockfighter.io/ob/api/ws/%s/venues/%s/%s' % (account, venue, socket_type)
    async with websockets.connect(url) as s:
        # await s.send(message)
        while True:
            print(socket_type, "looping")
            print(socket_type, await s.recv())



def main():
    account = "ACCOUNT#NUM"
    venue = "TESTEX"
    api_key = {"X-Starfighter-Authorization":"your key goes here"}
    stock = "FOO"

    loop = asyncio.get_event_loop()
    tasks = [
        loop.create_task(handle_stockfighter(account, venue, "executions")),
        loop.create_task(handle_stockfighter(account, venue, "tickertape")),
        loop.create_task(heartbeat(api_key)),
        loop.create_task(block_order(account, 1500, 10, "buy", api_key, venue, stock, "limit"))
    ]
    loop.run_until_complete(asyncio.gather(*tasks))


if __name__ == '__main__':
    main()



