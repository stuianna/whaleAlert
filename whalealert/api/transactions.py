import logging

log = logging.getLogger(__name__)


class Transactions():

    def __init__(self):
        pass

    def get_transactions(self, start_time, end_time, api_key, cursor, min_value, limit):
        success = False
        status = {}
        transactions = {}
        return success, transactions, status
