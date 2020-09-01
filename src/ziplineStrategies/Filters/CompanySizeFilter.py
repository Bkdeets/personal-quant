import numpy as np
from zipline.pipeline import CustomFilter
from pipeline_live.data.polygon.fundamentals import PolygonCompany

def isMidToLargeCap(lookback):
    class IsMidToLargeCap(CustomFilter):
        inputs = [PolygonCompany.marketcap]
        def compute(self, today, assets, out, marketcap):
            lower_limit = 2000000000.00 #2 billion
            mid_high_cap = marketcap > lower_limit
            out[:] = mid_high_cap
    return IsMidToLargeCap(window_length=lookback)