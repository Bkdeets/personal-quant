# {
#   "timestamp": "2018-04-01T12:00:00.000Z",
#   "is_open": true,
#   "next_open": "2018-04-01T12:00:00.000Z",
#   "next_close": "2018-04-01T12:00:00.000Z"
# }
import datetime
class MockClock
    def __init__(
        self,
        timestamp=datetime.datetime.now(),
        is_open=True,
        next_open=datetime.datetime.now(),
        next_close=datetime.datetime.now()
    ):
        self.timestamp = timestamp
        self.is_open = is_open
        self.next_open = next_open
        self.next_close = next_close
    
    ### non api functions ###
    def reset(timestamp):
        self.timestamp = timestamp
        self.is_open = self.checkOpen()
        self.next_open = self.getNextOpen()
        self.next_close = self.next_open + datetime.timedelta(hours=8)

    # TODO: Support weekends and market holidays
    ## Probably would involve an API call on init to get open days/times, storing it here and checking
    def checkOpen():
        openTime = datetime.time(9, 30, 0, 0)
        closeTime = datetime.time(16, 0, 0, 0)
        return openTime < self.timestamp.time() < closeTime

    # TODO: Implement this
    def getNextOpen():
        return False 
    

    