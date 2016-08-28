import requests # aiohttp
import numpy
import json
from ws4py.client.threadedclient import WebSocketClient


## Worry about later
# have 1+ accounts
# each account is in a venue
# each venue can have multiple stocks


# you can have buy and sell orders in these stocks

    # these orders can be limit, market, fill-or-kill, immediate-or-cancel
    # they can be partially filled, or completely filled



class Stockfighter(object):
    def __init__(self, api_key, venue, stock, account):
        self.api_key = api_key
        self.venue = venue
        self.stock = stock
        self.account = account

        # position = bought_orders - sold_orders
        self.position = 0

        # nav = worth_of_current_stocks + cash
        self.nav = 0

        # cash = sold_orders_worth - bought_orders_worth      
        self.cash = 0

        # all orders ever, keys = ids, values = (json order object, order_money)
        self.order_dict = {}

        self.non_complete_list = []

        self.init_info()
        self.quotes = []
        self.init_quotes()

        # #initial
        # tickertape_url = "wss://api.stockfighter.io/ob/api/ws/%s/venues/%s/tickertape/stocks/%s" % (self.account, self.venue, self.stock)
        # self.tickertape = websocket.create_connection(tickertape_url)


        # executions_url = 'wss://api.stockfighter.io/ob/api/ws/%s/venues/%s/executions' % (self.account, self.venue)
        # self.executions_sock = websocket.create_connection(executions_url)






    def init_info(self):
        print("initializing lists")
        orders = self.get_all_orders()

        if orders:
            # print "orders is good"
            for order in orders:
                # print "looking at order ", order["id"]
                if order["direction"] == "sell":
                    # self.position -= (order["originalQty"] - order["qty"])
                    (order_money, num_filled) = self.sum_fills(order["fills"])
                    self.cash += order_money
                    self.position -= num_filled

                if order["direction"] == "buy":
                    # self.position += (order["originalQty"] - order["qty"])
                    (order_money, num_filled) = self.sum_fills(order["fills"])
                    self.cash -= order_money
                    self.position += num_filled
                    
                # add to dictionary of things
                self.order_dict[order["id"]] = (order, order_money, num_filled)
                # if not filled, add id to list
                if bool(order["open"]):
                    self.non_complete_list.append(order["id"])




    def init_quotes(self):
        for i in range(5):
            self.quotes.append(self.quote())

    def block_order(self, price, quantity, buy_sell, order_type="limit"):
        order = json.dumps({"orderType":order_type, 
            "qty":quantity, 
            "direction":buy_sell, 
            "account":self.account, 
            "price":int(price), 
            "stock":self.stock,
            "venue":self.venue
            })
        order_url = "https://api.stockfighter.io/ob/api/venues/%s/stocks/%s/orders" % (self.venue, self.stock)

        order_response = self.request(order_url, order, "POST")
        # print "ORDER RESPONSE ", order_response
        if order_response['ok']:
            # print "adding to non_complete_list : ", order_response["id"]
            self.non_complete_list.append(order_response["id"])


    def update(self):
        print("~~~~updating~~~~")

        remove_list = []
        # go through order_ids in non_complete_list
        for i in range(len(self.non_complete_list)):

            # for each order, get current status from API
            order_id = self.non_complete_list[i]
            latest_order = self.order_status(order_id)

            # sum all filled orders
            (order_money, num_filled) = self.sum_fills(latest_order["fills"])

            # if the order id is not in the dictionary
            if not (order_id in self.order_dict):
                # add the order and the order money to the dictionary
                self.order_dict[order_id] = (latest_order, order_money, num_filled)
                
                if latest_order["direction"] == "sell":
                    self.position -= num_filled
                    self.cash += order_money
                if latest_order["direction"] == "buy":
                    self.position += num_filled
                    self.cash -= order_money
            else:
                (old_order, old_order_money, old_num_filled) = self.order_dict[order_id]        
                
                if old_order != latest_order:
                    pos_change = num_filled - old_num_filled
                    cash_change = abs(order_money - old_order_money)

                    if latest_order["direction"] == "sell":  
                        self.position -= pos_change
                        self.cash += cash_change
                    if latest_order["direction"] == "buy":    
                        self.position += pos_change
                        self.cash -= cash_change

            if not latest_order["open"]:
                remove_list.append(order_id)

        if remove_list:
            for order_id in remove_list:
                self.non_complete_list.remove(order_id)

        last_quote = self.quote()
        self.nav = (last_quote * self.position) + self.cash
        self.quotes.append(last_quote)

   
    



# {
#   "ok": true,
#   "quote": { // the below is the same as returned through the REST quote API
#     "symbol": "FAC",
#     "venue": "OGEX",
#     "bid": 5100, // best price currently bid for the stock
#     "ask": 5125, // best price currently offered for the stock
#     "bidSize": 392, // aggregate size of all orders at the best bid
#     "askSize": 711, // aggregate size of all orders at the best ask
#     "bidDepth": 2748, // aggregate size of *all bids*
#     "askDepth": 2237, // aggregate size of *all asks*
#     "last": 5125, // price of last trade
#     "lastSize": 52, // quantity of last trade
#     "lastTrade": "2015-07-13T05:38:17.33640392Z", // timestamp of last trade,
#     "quoteTime": "2015-07-13T05:38:17.33640392Z" // server ts of quote generation
#   }
# }

    def sum_fills(self, fills):
        money = 0
        num_filled = 0
        # print "called sum_fills"
        for fill in fills:
            # for fill in fill_list:
            money += fill["price"]*fill["qty"]
            num_filled += fill["qty"]
            # print money

        return (money, num_filled)


    def get_all_orders(self):
        url = "https://api.stockfighter.io/ob/api/venues/%s/accounts/%s/orders" % (self.venue, self.account)
        r = self.request(url)

        if r["ok"]:
            return r["orders"]


    def heartbeat(self):
        heartbeat = "https://api.stockfighter.io/ob/api/heartbeat"
        r = self.request(heartbeat)
        return bool(r['ok'])


    def request(self, url, data=None, method="GET"):
        if data is not None:
            res = requests.request(method, url, headers=self.api_key, data=data).json()
        else:
            res = requests.request(method, url, headers=self.api_key).json()

        if not res["ok"]:
            print("Response failed")
            print(res)
        return res


    def quote(self):
        url =  "https://api.stockfighter.io/ob/api/venues/%s/stocks/%s/quote" % (self.venue, self.stock)
        quote = self.request(url)

        if quote["ok"] == True:
            # print(quote)
            if "last" in quote:
                price = quote["last"]
                self.quotes.append(price)
                return price

        

    def order_status(self, order_id):
        url = order_url = "https://api.stockfighter.io/ob/api/venues/%s/stocks/%s/orders/%s" % (self.venue, self.stock, order_id)
        order = self.request(url)

        if order["ok"] == True:
            return order



    def spread(self):
        len_quotes = len(self.quotes)
        if len_quotes > 15:
            self.quotes = self.quotes[len_quotes-15:]

        q = self.quote()
        if q:
            self.quotes.append()

        if quotes:
            mean = numpy.mean(self.quotes)
            std = numpy.std(self.quotes)

        # low and high
            return (mean-std, mean+std)

        return (0,0)


# def market_update(self):
#         mu = self.tickertape.recv()
#         mu = json.loads(mu)

#         print "~~~~~~~~~~~~~~~~"
#         # print mu
#         if "bid" in mu:
#             print "bid: ", mu['quote']['bid']
#         if "ask" in mu:
#             print "ask: ", mu['quote']["ask"]
#         if "bidSize" in mu:
#             print "bidSize: ", mu['quote']["bidSize"]
#         if "askSize" in mu:
#             print "askSize: ", mu['quote']["askSize"]



#     def executions_update(self):

#         eu = self.executions_sock.recv()
#         eu = json.loads(eu)

#         print eu


# #initial
#         tickertape_url = "wss://api.stockfighter.io/ob/api/ws/%s/venues/%s/tickertape/stocks/%s" % (self.account, self.venue, self.stock)
#         self.tickertape = websocket.create_connection(tickertape_url)


#         executions_url = 'wss://api.stockfighter.io/ob/api/ws/%s/venues/%s/executions' % (self.account, self.venue)
#         self.executions_sock = websocket.create_connection(executions_url)





class OrderBook(object):
    def __init__(self, api_key, venue, stock, account):
        
        pass


class StockSocket(WebSocketClient):
    def opened(self):
        def data_provider():
            for i in range(1, 200, 25):
                yield "#" * i

        self.send(data_provider())

        for i in range(0, 200, 25):
            print(i)
            self.send("*" * i)

    def closed(self, code, reason=None):
        print("Closed down", code, reason)

    def received_message(self, m):
        print(m)
        if len(m) == 175:
            self.close(reason='Bye bye')





