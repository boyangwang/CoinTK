from cointk import init

from cointk.backtest import backtest
from HeresyStrategy import HeresyStrategy

strategy = HeresyStrategy()
backtest(strategy,
  initial_funds=10000,
  initial_balance=0,
  fill_prob=1,
  fee=0.002,
  train_prop=0.85,
  val_prop=0.15)