from cointk.init import init

from cointk.backtest import backtest
from strategies.HeresyStrategy import HeresyStrategy

init(force_download=False)

HeresyStrategyInstance = HeresyStrategy()

backtest(HeresyStrategyInstance,
  initial_funds=10000,
  initial_balance=1,
  fill_prob=1,
  fee=0.002,
  train_prop=0.99,
  val_prop=0.01,
  verbose=3, use_hour_data=True)