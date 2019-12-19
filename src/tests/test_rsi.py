from src.indicators.rsi import RSI
import statistics

class TestRSI:

    def test_initRS(self):
        period = 4
        prices = [1,2,1,2]
        ticker = 'whodunnit'

        rsi = RSI(period,prices,ticker)
        res = rsi.initRS()

        RS,avgsog,avgsol,gains,losses=res[0],res[1],res[2],res[3],res[4]

        assert RS == 2
        assert avgsog == .5
        assert avgsol == .25
        assert gains == [1,1]
        assert losses == [1]
    
    def test_calculate(self):
        period = 4
        prices = [1,1,3,1,1]
        ticker = 'whodunnit'
        rsi = RSI(period,prices,ticker)

        assert rsi.rsis[-1] == 50.0







