from cointk.init import init

from cointk.backtest import backtest
from HeresyStrategy import HeresyStrategy

init()

strategy = HeresyStrategy()
backtest(strategy,
  initial_funds=10000,
  initial_balance=0,
  fill_prob=1,
  fee=0.002,
  train_prop=0.99,
  val_prop=0.01,
  verbose=3)