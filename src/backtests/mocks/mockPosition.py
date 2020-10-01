# {
#   "asset_id": "904837e3-3b76-47ec-b432-046db621571b",
#   "symbol": "AAPL",
#   "exchange": "NASDAQ",
#   "asset_class": "us_equity",
#   "avg_entry_price": "100.0",
#   "qty": "5",
#   "side": "long",
#   "market_value": "600.0",
#   "cost_basis": "500.0",
#   "unrealized_pl": "100.0",
#   "unrealized_plpc": "0.20",
#   "unrealized_intraday_pl": "10.0",
#   "unrealized_intraday_plpc": "0.0084",
#   "current_price": "120.0",
#   "lastday_price": "119.0",
#   "change_today": "0.0084"
# }

class MockPosition:
    def __init__(
        self,
        asset_id="aUUID",
        symbol="ASYMBOL",
        exchange="NASDAQ",
        asset_class="us_equity",
        avg_entry_price=0.0,
        qty=0,
        side="long",
        market_value=0.0,
        cost_basis=0,
        unrealized_pl=0.0,
        unrealized_plpc=0.0,
        unrealized_intraday_pl=0.0,
        unrealized_intraday_plpc=0.0,
        current_price=0.0,
        lastday_price=0.0,
        change_today=0.0
    ):
        self.asset_id = asset_id
        self.symbol = symbol
        self.exchange = exchange
        self.asset_class = asset_class
        self.avg_entry_price = avg_entry_price
        self.qty = qty
        self.side = side
        self.market_value = market_value
        self.cost_basis = cost_basis
        self.unrealized_pl = unrealized_pl
        self.unrealized_plpc = unrealized_plpc
        self.unrealized_intraday_pl = unrealized_intraday_pl
        self.unrealized_intraday_plpc = unrealized_intraday_plpc
        self.current_price = current_price
        self.lastday_price = lastday_price
        self.change_today = change_today