from cointk.strategies.core import Strategy
from cointk.order import Order

def compare_with_delta(a, b, delta = 0.003):
  delta = (a / 2 + b / 2) * delta
  if a - b > delta:
    return 1
  elif a - b < -delta:
    return -1
  else:
    return 0

def generate_signals(all_prices):
  if all_prices is None:
    print('XXX all_prices is None')
    return []

  print('XXX len of all_prices', len(all_prices))
  print('XXX all_prices sample', all_prices[0:5])
  signals = []

  index = 0
  nextIndex = 1
  currentDirection = 'sell'
  # Now start the loop
  while nextIndex < len(all_prices):
    print('XXX index at {} of ts {}'.format(index, all_prices[index]))
    # while price no big change, proceed
    while (nextIndex < len(all_prices) and
      compare_with_delta(all_prices[index][1], all_prices[nextIndex][1]) == 0):
      nextIndex += 1
    
    # if we fall out because length exausted, break
    if nextIndex >= len(all_prices):
      break
    
    # else we fall out because of major change. Find direction
    if compare_with_delta(all_prices[index][1], all_prices[nextIndex][1]) == 1:
      # next is lower
      if currentDirection == 'sell':
        print('Want to sell but already empty, continue')
      else:
        print('Adding {} signal at ts {}, current price {}, target price {}'.format(
          'sell', all_prices[index][0], all_prices[index][1], all_prices[nextIndex][1]))
        signals.append({'price': all_prices[index][1], 'index': index, 'ts': all_prices[index][0], 'buy': False})
        currentDirection = 'sell'
    elif compare_with_delta(all_prices[index][1], all_prices[nextIndex][1]) == -1:
      # next is higher
      if currentDirection == 'buy':
        print('Want to buy but already full, continue')
      else:
        print('Adding {} signal at ts {}, current price {}, target price {}'.format(
          'buy', int(all_prices[index][0]), all_prices[index][1], all_prices[nextIndex][1]))
        signals.append({'price': all_prices[index][1], 'index': index, 'ts': all_prices[index][0], 'buy': True})
        currentDirection = 'buy'
    else:
      print('XXX next is not significantly different than current. Should never happen')
    
    index = nextIndex
    nextIndex = index + 1

  print('XXX signals', signals)
  return signals

class HeresyStrategy(Strategy):
  def __init__(self, price_inc=0.1):
    super().__init__()
    self.price_inc = price_inc
    self.signals = None

  def gen_order(self, ts, price, qty, cash_funds, btc_balance, all_prices=None):
    # one-time op
    if self.signals is None:
      self.signals = generate_signals(all_prices)

    if len(self.signals) == 0:
      return None
    nextOrder = self.signals[0]
    if nextOrder['ts'] == ts and nextOrder['price'] == price:
      self.signals = self.signals[1:]
      
      orderPrice = (price + self.price_inc) if nextOrder['buy'] else price - self.price_inc
      orderQty = (cash_funds / orderPrice) * 0.95 if nextOrder['buy'] else btc_balance

      enrichedNextOrder = Order(buy=nextOrder['buy'], sell=(not nextOrder['buy']), price=orderPrice,
        qty=orderQty, identifier=len(self.orders))
      return enrichedNextOrder
    else:
      return None
