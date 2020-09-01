
from pipeline_live.engine import LivePipelineEngine
from pipeline_live.data.alpaca.pricing import USEquityPricing
from pipeline_live.data.sources.polygon import list_symbols
from zipline.pipeline import Pipeline
from src.ziplineStrategies.Filters.CurVsAvgVolFilter import curVsAvgVolFilter
from src.ziplineStrategies.Filters.CompanySizeFilter import isMidToLargeCap
from pipeline_live.data.iex.factors import (AverageDollarVolume, SimpleMovingAverage)
from pylivetrader.api import(
    symbol,
    pipeline_output,
    attach_pipeline,
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

    attach_pipeline(
        make_pipeline(context), 
        name='smaCrossPipeline'
    )

def make_pipeline(context):
    advFilter = curVsAvgVolFilter(context.params.get('lookback'))
    midToLargeFilter = isMidToLargeCap(context.params.get('lookback'))
    smaSlow = SimpleMovingAverage(
        inputs=[USEquityPricing.close],
        window_length=context.params.get('smaSlowLookback'))
    smaFast = SimpleMovingAverage(
        inputs=[USEquityPricing.close],
        window_length=context.params.get('smaFastLookback'))

    pipe = Pipeline()
    pipe.add(midToLargeFilter, 'midToLargeFilter')
    pipe.add(advFilter, 'advFilter')
    pipe.add(smaSlow, 'smaSlow')
    pipe.add(smaFast, 'smaFast')

    return pipe

def handle_data(context, data):
    numOfPositions = len(context.portfolio.positions)
    pr = ENGINE.run_pipeline(make_pipeline(context))
    filtered = applyPipelineFilters(pr)
    if not filtered.empty:
        for asset, value in filtered.iterrows():
            asset = symbol(asset)
            currentPrice = data.current(asset, "close")
            stopPrice = currentPrice * context.stopLevel
            if longConditionsMet(value, currentPrice):
                # enter position with position size as long as leverage is below certain level
                if withinLeverageLimit(context, numOfPositions):
                    logging.info(f'Ordering shares of {asset} at {currentPrice} with a stop at {stopPrice}')
                    order_target_percent(asset, context.position_size, stop_price=stopPrice)
                    numOfPositions += 1
            elif asset in context.portfolio.positions.keys():
                logging.info(f'Exiting position in {asset}')
                order_target_percent(asset, 0.0)

def withinLeverageLimit(context, numOfPositions):
    return (numOfPositions/(context.position_size * 100)) < context.leverageLimit

def longConditionsMet(value, currentPrice):
    return value['smaFast'] < value['smaSlow'] and value['smaSlow'] > currentPrice

def applyPipelineFilters(pr):
    pr = pr[pr['advFilter']]
    pr = pr[pr['midToLargeFilter']]
    return pr
