# @marfedora, August 2016

# A small toy example of current concurrent websockets to the stockfighter API
# Tickertape runs constantly, executions prints as the order fills take place

async def handle_stockfighter(account, venue, socket_type):

    url = 'wss://api.stockfighter.io/ob/api/ws/%s/venues/%s/%s' % (account, venue, socket_type)
    async with websockets.connect(url) as s:
        while True:
            print(socket_type, "looping")
            print(socket_type, await s.recv())



def main():
    account = "ACCOUNT#NUM"
    venue = "TESTEX"
    api_key = {"X-Starfighter-Authorization":"your key goes here"}
    stock = "FOO"

    # handle the event loop
    loop = asyncio.get_event_loop()
    tasks = [
        loop.create_task(handle_stockfighter(account, venue, "executions")),
        loop.create_task(handle_stockfighter(account, venue, "tickertape")),
    ]
    loop.run_until_complete(asyncio.gather(*tasks))


if __name__ == '__main__':
    main()

