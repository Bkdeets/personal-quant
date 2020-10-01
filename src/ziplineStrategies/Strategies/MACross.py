
from pipeline_live.engine import LivePipelineEngine
from pipeline_live.data.alpaca.pricing import USEquityPricing
from pipeline_live.data.alpaca.factors import AverageDollarVolume
from pipeline_live.data.sources.polygon import list_symbols
from zipline.pipeline import Pipeline
from src.ziplineStrategies.Filters.CurVsAvgVolFilter import curVsAvgVolFilter
# from src.ziplineStrategies.Filters.CompanySizeFilter import isMidToLargeCap

from pipeline_live.data.iex.factors import SimpleMovingAverage
from pylivetrader.api import(
    symbol,
    pipeline_output,
    order_target_percent)
import logging

ENGINE = LivePipelineEngine(list_symbols)

def initialize(context):
    context.params = {
        'lookback': 20,
        'smaSlowLookback': 30,
        'smaFastLookback': 10
    }
    context.position_size = .1
    context.stopLevel = .9
    context.leverageLimit = 1.5
    context.stopPriceMap = {}

def make_pipeline(context):
    advFilter = curVsAvgVolFilter(context.params.get('lookback'))
    # midToLargeFilter = isMidToLargeCap(context.params.get('lookback'))
    smaSlow = SimpleMovingAverage(
        inputs=[USEquityPricing.close],
        window_length=context.params.get('smaSlowLookback'))
    smaFast = SimpleMovingAverage(
        inputs=[USEquityPricing.close],
        window_length=context.params.get('smaFastLookback'))
    top50 = AverageDollarVolume(window_length=20).top(50)

    pipe = Pipeline(screen=top50)
    pipe.add(advFilter, 'advFilter')
    pipe.add(smaSlow, 'smaSlow')
    pipe.add(smaFast, 'smaFast')
    # pipe.add(midToLargeFilter, 'midToLargeFilter')

    return pipe

def handle_data(context, data):
    pr = ENGINE.run_pipeline(make_pipeline(context))
    filtered = applyPipelineFilters(pr)
    entryAndExitLogic(context, data, filtered)
    # manageStops(context, data)

def entryAndExitLogic(context, data, filtered):
    numOfPositions = len(context.portfolio.positions)
    if not filtered.empty:
        for asset, value in filtered.iterrows():
            asset = symbol(asset)
            currentPrice = data.current(asset, 'close')
            # stopPrice = currentPrice * context.stopLevel
            if longConditionsMet(value, currentPrice):
                # enter position with position size as long as leverage is below certain level
                if withinLeverageLimit(context, numOfPositions):
                    logging.info(f'Ordering shares of {asset} at {currentPrice}')
                    # context.stopPriceMap[asset] = stopPrice
                    order_target_percent(asset, context.position_size)
                    numOfPositions += 1
            elif asset in context.portfolio.positions.keys():
                logging.info(f'Exiting position in {asset}')
                if not asset == symbol('NCNO'):
                    order_target_percent(asset, 0.0)

def manageStops(context, data):
    for asset, value in context.portfolio.positions.items():
        stopPrice = context.stopPriceMap[asset]
        currentPrice = data.current(asset, 'close')
        newStop = currentPrice * context.stopLevel
        if currentPrice < stopPrice:
            logging.info(f'Stopped out of {asset}')
            order_target_percent(asset, 0.0)
        elif newStop > stopPrice:
            context.stopPriceMap[asset] = newStop

def withinLeverageLimit(context, numOfPositions):
    return (numOfPositions/(context.position_size * 100)) < context.leverageLimit

def longConditionsMet(value, currentPrice):
    return value['smaFast'] < value['smaSlow'] and value['smaSlow'] > currentPrice

def applyPipelineFilters(pr):
    pr = pr[pr['advFilter']]
    return pr
