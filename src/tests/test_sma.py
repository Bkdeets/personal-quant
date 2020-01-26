from src.indicators.sma import SMA
import statistics

class TestSMA:

    def test_calculate(self):
        period = 4
        prices = [1,2,3,4]
        ticker = 'It Dont mattah lol'
        sma = SMA(period,prices,ticker)     

        assert sma.smas == [0,0,0,2.5]
        assert sma.apds == [
            (0, 0), (0, 0), (0, 0), (0.15, 0.3)
        ]
