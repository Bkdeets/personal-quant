import numpy as np

from zipline.pipeline import CustomFilter
from pipeline_live.data.alpaca.pricing import USEquityPricing

def curVsAvgVolFilter(lookback):
    class CurVsAvgVolFilter(CustomFilter):
        inputs = [USEquityPricing.close, USEquityPricing.volume]
        def compute(self, today, assets, out, close_price, volume):
            avg_dollar_volume = np.mean(close_price * volume, axis=0)
            current_dollar_volume = close_price[-1] * volume[-1]
            high_volume = current_dollar_volume > avg_dollar_volume
            out[:] = high_volume
    return CurVsAvgVolFilter(window_length=lookback)