from src.utility.utility import Utility
import statistics

class TestUtility:

    def test_calc_eps_growth_no_changes(self):
        fundamentals = [{'nothing to see here':0}]
        assert Utility().calc_eps_growth(fundamentals) == 0

    def test_calc_eps_growth_happy(self):
        fundamentals = [{
            'earningsPerBasicShare': 10
        },{
            'earningsPerBasicShare': 20
        }]
        assert Utility().calc_eps_growth(fundamentals) == 1

    def test_calc_cost_of_equity(self):
        fundamental = {'ticker': 'AAPL'}
        result = Utility().calc_cost_of_equity(fundamental)
        assert result != None
    
    def test_calc_mos(self):
        assert Utility().calc_mos(100,100) == 0
    
    def test_get_risk_free_rate(self):
        assert Utility().get_risk_free_rate() == .015
    
    def test_get_market_return(self):
        assert Utility().get_market_return() == .1
    
    def test_calc_tax_rate_pass(self):
        fundamental = {
            'earningsBeforeTax': 100,
            'taxLiability': 50
        }
        result = Utility().calc_tax_rate(fundamental)
        assert result == .50
    
    def test_calc_tax_rate_except(self):
        fundamental = {'ticker': 'AAPL'}
        result = Utility().calc_tax_rate(fundamental)
        assert result == .15
    
    def test_get_cost_of_debt_happy(self):
        fundamental = {
            'interestExpense': 10,
            'debt': 20
        }
        result = Utility().get_cost_of_debt(fundamental)
        assert result == .5

    def test_get_cost_of_debt_sad(self):
        fundamental = {
            'interestExpense': 10,
            'debt': 0
        }
        result = Utility().get_cost_of_debt(fundamental)
        assert not result        
    
    def test_calc_wacc_happy(self):
        fundamental = {
            'ticker': 'AAPL',
            'interestExpense': 10,
            'debtToEquityRatio': 10,
            'debt': 10
        }
        result = Utility().calc_wacc(fundamental)
        assert result != None
    
    def test_calc_wacc_sad(self):
        fundamental = {
            'ticker': 'AAPL',
            'debtToEquityRatio': 10
        }
        result = Utility().calc_wacc(fundamental)
        assert not result

    def test_calc_dividend_growth_rate_happy(self):
        ticker = 'AAPL'
        limit = 1
        result = Utility().calc_dividend_growth_rate(ticker, limit=limit)
        assert result != None

    def test_calc_fcf_growth_happy(self):
        fundamentals = [{
            'ticker': 'AAPL',
            'freeCashFlow': 10
        },{
            'ticker': 'AAPL',
            'freeCashFlow': 20
        }]
        result = Utility().calc_fcf_growth(fundamentals)
        assert result == 1
    
    def test_calc_fcf_growth_sad(self):
        fundamentals = []
        result = Utility().calc_fcf_growth(fundamentals)
        assert not result

    def test_calc_avg_fcf_happy(self):
        fundamentals = [{
            'ticker': 'AAPL',
            'freeCashFlow':100},
            {
            'ticker': 'AAPL',
            'freeCashFlow':100}]
        result = Utility().calc_avg_fcf(fundamentals)
        assert result == 100

    def test_calc_avg_fcf_sad(self):
        fundamentals = []
        result = Utility().calc_avg_fcf(fundamentals)
        assert not result

    def test_calc_residual_income_happy(self):
        fundamental = {
            'ticker': 'AAPL',
            'netIncome': 100,
            'shareholdersEquity': 100
        }
        result = Utility().calc_residual_income(fundamental)
        assert result != None
    
    def test_calc_residual_income_sad(self):
        fundamental = {'ticker': 'AAPL'}
        result = Utility().calc_residual_income(fundamental)
        assert not result

    def test_calc_residual_income_growth_happy(self):
        fundamentals = [{
            'ticker': 'AAPL',
            'netIncome': 100,
            'shareholdersEquity': 100
        },
        {
            'ticker': 'AAPL',
            'netIncome': 100,
            'shareholdersEquity': 100
        }]
        result = Utility().calc_residual_income_growth(fundamentals)
        assert result == 0

    def test_calc_residual_income_growth_no_fundamentals(self):
        fundamentals = []
        result = Utility().calc_residual_income_growth(fundamentals)
        assert not result