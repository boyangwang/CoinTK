from random import random
from plotly.offline import plot
import plotly.graph_objs as go
from .data import load_data, subarray_with_stride, to_datetimes
import time
import numpy as np
import pprint
from copy import deepcopy

'''
 main code for running backtests and graphing results
'''
def resolve_data(data, fnm, name, datapart,
                 train_prop, val_prop):
    '''
        Either read in the dataset or use a caller-provided one
    '''
    if data is not None:
        return data
    train_data, val_data, test_data = load_data(fnm, name,
                                                train_prop, val_prop)
    if datapart == 'train':
        return train_data
    elif datapart == 'val':
        return val_data
    elif datapart == 'test':
        return test_data


def backtest(strategy, initial_funds=1000, initial_balance=0, fill_prob=0.5,
             fee=0.0025, data=None, data_fnm='data/coinbaseUSD.npz',
             history_fnm='histories/backtest.npz',
             data_name='data', datapart='val',
             plot_fnm='temp-plot.html', use_hour_data = False,
             train_prop=0.8, val_prop=0.1, verbose=1, plot_freq=10000, plot_args={}):

    '''
        Runs backtest for a given strategy on historical dataset and output its decisions and results.
        Note that because of fill_prob, to get deterministic results you should call random.seed
        with the same seed before every run.


            fill_prob determines the probability that an order will fail, to simulate real market competitions

            fee is the fraction of transaction fee
            
            history_fnm is used for the Bitbox-Server

            train_prop and val_prop, each a fraction adding to less than 1, determine the size of the training & testing sets.
              The rest is the testing set

            datapart determines which part of the data (train/val/test) we are running on


            plot_args is any additional optional arguments we pass to additonal_plots

        About train, val, test

            By default, it uses validation date set, and that would be the 80% - 90%,
            in terms of time serie. That's not useful for my use case.
            So set val=0.15, train=0.85 (that is, ignore=0.85, test=0.15)
    '''

    input_args = locals()  # save the input arguments for logging
    strategy_args = deepcopy(strategy.__dict__)

    # default to validation
    data = resolve_data(data, data_fnm, data_name, datapart, val_prop=val_prop, train_prop=train_prop)
    if verbose:
        print("data size: ", data.shape)
    

    time1 = time.time()

    funds = initial_funds  # US dollars
    fund_history = [funds]
    balance = initial_balance  # bitcoin amounts
    balance_history = [balance]
    initial_worth = initial_funds + initial_balance * data[0][1]
    worth = initial_worth  # total value converted to dollars
    worth_history = [worth]
    balance_worth_history = [balance * data[0][1]]
    ts_history = [data[0][0]]
    strategy.init_backtest(funds, balance, initial_worth)

    # each tuple is the log of an actual transaction at timestamp ts for the
    # listed price/qty

    # we don't have historical data on the order book, so we can only infer
    # what kind of order/sell strategy would have worked based on the actual
    # transactions.
    # Namely, if we sell at a lower price or buy at a higher price
    # for the same or less quantity, we should succeed
    time2 = time.time()

    for i, (ts, price, qty) in enumerate(data[:-1]):
        # print('Doing backtest on i {} ts {} price {} qty {}'.format(
        #     i, ts, price, qty))
        if verbose > 1 and i % plot_freq == 0:
            print(i, ('worth', worth, 'balance', balance, 'funds', funds))

        next_ts, next_price, next_qty = data[i+1]
        order = strategy.evaluate(ts, price, qty, funds, balance, data)
        if order is None or order.empty:
            continue

        # in real markets there's a chance that your order won't succeed, say
        # if someone beats you to buying;
        # so we use fill_prob to simulate that "fail chance"

        # this essentially estimates the chance that if we send the same
        # next-historical-transaction, we'll get the deal first
        if random() > fill_prob:
            strategy.reject_order(order.identifier)
            continue

        # try to buy
        if order.buy:
            # we can only guarantee buying if our price is higher than the
            # historical transacted price
            if not order.price >= price:
                if verbose > 2:
                    print('price too low')
                strategy.reject_order(order.identifier)
                continue
            else:
                # we can only guarantee a quantity based on historical
                # transactions
                # filled_qty = min(order.qty, next_qty)

                # cancel this limitation for now
                filled_qty = order.qty
                
                filled_price = price
                if filled_price * filled_qty > funds:
                    if verbose > 2:
                        print('insufficient funds')
                    strategy.reject_order(order.identifier)
                    continue
                fund_delta = -filled_price * filled_qty
                balance_delta = filled_qty

        # try to sell; same limitations apply as above
        if order.sell:
            if not order.price <= price:
                if verbose > 2:
                    print('price too high')
                strategy.reject_order(order.identifier)
                continue
            else:
                # filled_qty = min(order.qty, next_qty)

                # cancel this limitation for now
                filled_qty = order.qty
                filled_price = price
                if filled_qty > balance:
                    if verbose > 2:
                        print('insufficient balance')
                    strategy.reject_order(order.identifier)
                    continue
                fund_delta = filled_price * filled_qty
                balance_delta = -filled_qty

        # if order succeeded
        strategy.fill_order(order.identifier, filled_price, filled_qty)
        funds -= filled_price * filled_qty * fee  # pay transaction fee
        funds += fund_delta
        balance += balance_delta

        # historical tracking of what our algorithm predicts
        fund_history.append(funds)
        balance_history.append(balance)
        ts_history.append(next_ts)
        worth = funds + balance * next_price
        worth_history.append(worth)
        balance_worth_history.append(balance * next_price)

    ts_history.append(data[-1][0])
    worth_history.append(worth)
    balance_worth_history.append(balance * next_price)
    fund_history.append(funds)

    time3 = time.time()

    if verbose > 0:
        print('=' * 50)
        print('Backtest summary for:')
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(input_args)
        print('Strategy initial args:')
        pp.pprint(strategy_args)
        print('Funds: {} -> {}'.format(initial_funds, funds))
        print('Balance: {} -> {}'.format(initial_balance, balance))
        print('Net worth: {} -> {}'.format(initial_worth, worth))
        buy_hold_worth = (initial_funds / data[0][1]
                          + initial_balance) * data[-1][1]
        print('Buy hold equivelent: {} -> {}'.format(initial_worth,
                                                     buy_hold_worth))

    # plot every plot_freq data points
    plot_data = subarray_with_stride(data, plot_freq)

    # by default, we plot the buy-hold equivalent value and algorithm performance,
    # the latter sectioned into liquid (cash) and nonliquid (Bitcoin) assets
    results = [{'x': to_datetimes(plot_data[:, 0]),
                'y': initial_funds * plot_data[:, 1] / plot_data[0, 1],
                'name': 'Buy-hold net worth (Bitcoin Price scaled)',
                'line': dict(width=2.0)},
               {'x': to_datetimes(ts_history),
                'y': balance_worth_history,
                'name': 'Algorithm Nonliquid Bitcoin Worth',
                'fill': 'tozeroy',
                'line': dict(color='rgb(111, 231, 219)')},
               {'x': to_datetimes(ts_history),
                'y': worth_history,
                'name': 'Algorithm Net Worth (Bitcoin + Cash)',
                'fill': 'tonexty',
                'line': dict(width=0.5, color='rgb(184, 247, 212)')}]

    # print(plot_data.shape)
    buy_hold_ts_history = plot_data[:, 0]
    buy_hold_eq_history = initial_funds * plot_data[:, 1] / plot_data[0, 1]

    # we can add additional plots as defined in the Strategy class passed in
    # e.g. graphing the MA for moving-average algorithms
    results += strategy.additional_plots(plot_freq, plot_args)

    if plot_fnm is not None:
        plot_results(results, plot_fnm)

    time4 = time.time()

    if verbose > 0:
        print('Time to load data: {}s'.format(time2 - time1))
        print('Time to train: {}s, {}s per 1000 ticks'.format(
            time3 - time2, (time3 - time2)/len(data)))

        print('Time to plot: {}s'.format(time4-time3))

    np.savez(history_fnm, ts_history=np.asarray(ts_history, dtype='int32'),
             buy_hold_eq_history=buy_hold_eq_history,
             buy_hold_ts_history=np.asarray(buy_hold_ts_history,
                                            dtype='int32'),
             worth_history=worth_history,
             balance_worth_history=balance_worth_history)

    return dict(fund_history=fund_history,
                balance_history=balance_history,
                ts_history=ts_history,
                worth_history=worth_history)


def plot_results(results, plot_name='temp-plot.html'):
    '''
        results is a list of dictionaries, each of which defines a trace
         e.g. [{'x': x_data, 'y': y_data, 'name': 'plot_name'}, {...}, {...}]

        Each dictionary's key-value pairs will be passed into go.Scatter
         to generate a trace on the graph

    '''
    traces = []

    for input_args in results:
        traces.append(go.Scatter(**input_args))

    layout = go.Layout(
        title='Trading performance over time',
        yaxis=dict(
            title='Value (USD)'
        ),
    )
    plot(go.Figure(data=traces, layout=layout), filename=plot_name)
