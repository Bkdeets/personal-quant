class MockAccount:

    def __init__(
        self,
        account_blocked=False,
        account_number=0,
        buying_power=0,
        cash=0,
        created_at=0,
        currency='USD',
        daytrade_count=0,
        daytrading_buying_power=0,
        equity=0,
        id=0,
        initial_margin=0,
        last_equity=0,
        last_maintenance_margin=0,
        long_market_value=0,
        maintenance_margin=0,
        multiplier=0,
        pattern_day_trader=False,
        portfolio_value=0,
        regt_buying_power=0,
        short_market_value=0,
        shorting_enabled=True,
        sma=0,
        status='ACTIVE',
        trade_suspended_by_user=False,
        trading_blocked=False,
        transfers_blocked=False
    ):
        self.account_blocked = account_blocked
        self.account_number = account_number
        self.buying_power = buying_power
        self.cash = cash
        self.created_at = created_at
        self.currency = currency
        self.daytrade_count = daytrade_count
        self.daytrading_buying_power = daytrading_buying_power
        self.equity = equity
        self.id = id
        self.initial_margin = initial_margin
        self.last_equity = last_equity
        self.last_maintenance_margin = last_maintenance_margin
        self.long_market_value = long_market_value
        self.maintenance_margin = maintenance_margin
        self.multiplier = multiplier
        self.pattern_day_trader = pattern_day_trader
        self.portfolio_value = portfolio_value
        self.regt_buying_power = regt_buying_power
        self.short_market_value = short_market_value
        self.shorting_enabled = shorting_enabled
        self.sma = sma
        self.status = status
        self.trade_suspended_by_user = trade_suspended_by_user
        self.trading_blocked = trading_blocked
        self.transfers_blocked = transfers_blocked
    