from ..utility import value_funcs as vf
class TestValueFuncs:
    
    # need polygon mock to test
    def test_calc_dd_model(self):
        fundamentals = [{
            'ticker': 'AAPL'
        }]
        result = vf.calc_dd_model(fundamentals)
        assert not result
    
    # need polygon mock to test
    def test_calc_fcf_model(self):
        fundamentals = [{
            'ticker': 'AAPL'
        }]
        result = vf.calc_fcf_model(fundamentals)
        assert not result
    
    # need polygon mock to test
    def test_calc_gd_model(self):
        fundamentals = [{
            'ticker': 'AAPL',
            'earningsPerBasicShareUSD': 100
        }]
        result = vf.calc_gd_model(fundamentals)
        assert not result
    
    # need polygon mock to test
    def test_calc_ri_model(self):
        fundamentals = [{
            'ticker': 'AAPL'
        }]
        result = vf.calc_ri_model(fundamentals)
        assert not result
    
    # need polygon mock to test
    def test_calc_models(self):
        fundamentals = [{
            'ticker': 'AAPL',
            'earningsPerBasicShareUSD': 100
        }]
        result = vf.calc_models(fundamentals)
        assert not result

