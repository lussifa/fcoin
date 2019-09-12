#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
from fcoin3 import Fcoin
import threading
import time
from multiprocessing.dummy import Pool as ThreadPool

# pubilc
retryt = 5
gate_symbol = 'BTC_USD'
fc_symbol = 'btcusdt'
sym = fc_symbol[0:-4]
fc_ordersize = 0.0222

# fcoin
fcoin = Fcoin()
fcoin.auth('', '')

def cancel_order(id):
    fcoin.cancel_order(id)

def cancel_all():
    pool = ThreadPool(6) 
    set=[]
    sell_list=[]
    sell_order_price=0
    sell_order_price_list=[]
    order_list = fcoin.list_orders(symbol=fc_symbol, states='submitted')
    order_list=order_list['data']
    order_num=(len(order_list))
    for order in order_list:
        set=set+[order['id']]
    pool.map(cancel_order,set)
    pool.close() 
    pool.join()
    
def get_chart():
    global chart
    fc_chart = fcoin.get_candle('M5', fc_symbol)
    chart = fc_chart['data']

def get_fc_price():
    global fc_bid
    global fc_ask
    ticker = fcoin.get_market_ticker(symbol=fc_symbol)
    try:
        ticker = ticker['data']['ticker']
        fc_bid = float(ticker[2])
        fc_ask = float(ticker[4])
    except:
        pass
    
def get_fc_balance():
    global allusdt
    global allcoin
    global freecoin
    global freeusdt
    total = fcoin.get_balance()
    total = total['data']
    for t in total:
        if t['currency'] == 'usdt':
            freeusdt = float(t['available'])
            allusdt = float(t['balance'])
        if t['currency'] == sym:
            freecoin = float(t['available'])
            allcoin = float(t['balance'])
    
    
def ft_sell(price):
    fcoin.sell(fc_symbol, price, fc_ordersize)
    
def ft_buy(price):
    fcoin.buy(fc_symbol, price, fc_ordersize)

def scalping():
    get_chart()
    global slow
    global timestamp
    global fast
    a=0
    fast=0
    slow=0
    timestamp=chart[0]['id']
    for i in chart:
        a=a+1
        fast=fast+float(i['close'])
        if a>=7:
            break
    fast=fast/7
    a=0
    for i in chart:
        a=a+1
        slow=slow+float(i['close'])
        if a>=15:
            break
    slow=slow/15
    

def sell_manager(direction):
    order_list = fcoin.list_orders(symbol=fc_symbol, states='filled')
    order_list=order_list['data']
    if direction=='short':
        fill_price=order_list[0]['price']
        fcoin.buy(fc_symbol, round(fill_price-1,1), fc_ordersize)
        time.sleep(1)
    if direction=='long':
        fill_price=order_list[0]['price']
        fcoin.sell(fc_symbol, round(fill_price+1,1), fc_ordersize)
        time.sleep(1)
    
def seller():
    retryt=0
    if freecoin>fc_ordersize:
        order_id=fcoin.sell(fc_symbol, round(fc_ask+1.1,1), fc_ordersize)['data']
        order_state=fcoin.order_result(order_id)['data']
        while order_state==[]:
            order_state=fcoin.order_result(order_id)['data']
            retryt=retryt+1
            time.sleep(0.3)
            print ('waiting for sell order filled', retryt)
            if retryt>8:
                try:
                    fcoin.cancel_order(order_id)
                except:
                    pass
                break
        order_state=fcoin.order_result(order_id)['data']
        if order_state!=[]:
            price=float(order_state[0]['price'])
            fcoin.buy(fc_symbol, round(price-1,1), fc_ordersize)

def buyer():
    retryt=0
    if freeusdt>fc_ordersize*fc_ask:
        order_id=fcoin.buy(fc_symbol, round(fc_bid-1.1,1), fc_ordersize)['data']
        order_state=fcoin.order_result(order_id)['data']
        while order_state==[]:
            order_state=fcoin.order_result(order_id)['data']
            retryt=retryt+1
            time.sleep(0.3)
            print ('waiting for buy  order filled', retryt)
            if retryt>8:
                try:
                    fcoin.cancel_order(order_id)
                except:
                    pass
                break
        order_state=fcoin.order_result(order_id)['data']
        if order_state!=[]:
            price=float(order_state[0]['price'])
            fcoin.sell(fc_symbol, round(price+1,1), fc_ordersize)

def trader():
    if fast>=slow+1:
        buyer()
    if fast<=slow-1:
        seller()
        
cancel_all()
get_fc_balance()
init_amount=int(allcoin*fc_bid+allusdt)
a=0
while 1:
    a=a+1
    '''if a%31==0:
        scalping()
        cancel_all()'''
    t1 = threading.Thread(target=get_fc_price)
    if not t1.is_alive():
        try:
            t1.start()
            t1.join()
        except:
            pass
    t2 = threading.Thread(target=get_fc_balance)
    if not t2.is_alive():
        try:
            t2.start()
            t2.join()
        except:
            pass
    t3 = threading.Thread(target=buyer)
    if not t3.is_alive():
        try:
            t3.start()
            t3.join()
        except:
            pass
    t4 = threading.Thread(target=seller)
    if not t4.is_alive():
        try:
            t4.start()
            t4.join()
        except:
            pass
    profit=int(allcoin*fc_bid+allusdt)-init_amount
    print ('price:',round((fc_bid+fc_ask)/2,1),' profit:',round(profit,2),' coin:',round(allcoin,4),' usdt:',round(allusdt,2))
    time.sleep(0.5)
