from cointk.strategies.core import Strategy
from collections import deque
from cointk.order import Order

class HeresyStrategy(Strategy):
  def __init__(self):
    super().__init__()
    self.old_prices = deque()

  def gen_order(self, ts, price, qty, funds, balance):
    # print('ts, price, qty, funds, balance', ts, price, qty, funds, balance)
    order = None
    self.old_prices.append(price)
    return order
