
from cointk.strategies.core import Strategy
from cointk.order import Order
import numpy
import pandas as pd
import math as m
from datetime import datetime, timedelta

ONE_HOUR = timedelta(hour=1)

class ObvMacdStrategy(Strategy):
  def __init__(self, num_init_ticks=30, ):
    super().__init__()
    # first see this many prices and calc before action
    self.num_init_ticks = num_init_ticks
    self.historical_prices = {
      volumes: [],
      prices: [],
    }

  def gen_order(self, ts, price, qty, cash_funds, btc_balance, all_prices=None):

    current_time = datetime(ts)

    # to know from which hour we started
    if self.start_hour is None:
      self.start_hour = datetime(ts)
      print('start_hour ' + self.start_hour)
      self.accumulating_hour = self.start_hour
    
    if current_time - self.accumulating_hour > ONE_HOUR:
      self.accumulating_hour = current_time
    else:
      self.accumulating_volume 
    # now we have 30 prices in history

    return None