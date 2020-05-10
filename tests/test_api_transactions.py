import unittest
from unittest import mock
import json
import time
import logging
from requests.models import Response
from requests import Session
from requests.exceptions import Timeout, TooManyRedirects
import whalealert.settings as settings
from whalealert.api.transactions import Transactions

logging.disable(logging.CRITICAL)

text_error = {"result": "error", "message": "invalid api_key"}
text_error_bad_key = {"result": "error", "bad_key": "invalid api_key"}
text_empty = {"result": "success", "cursor": "2712e8b6-2712e8b6-5eafc647", "count": 0}
text_empty_bad_key = {"result": "success", "bad_key": "2712e8b6-2712e8b6-5eafc647", "count": 0}
text_success = {
    "result":
    "success",
    "cursor":
    "2712f286-2712f286-5eafc711",
    "count":
    2,
    "transactions": [{
        "blockchain": "ethereum",
        "symbol": "usdt",
        "id": "655552612",
        "transaction_type": "transfer",
        "hash": "4cdfc57c737b4214fbce384e57f50d8b52f80c2eb470654f9fdc2062c534bf42",
        "from": {
            "address": "477b8d5ef7c2c42db84deb555419cd817c336b6f",
            "owner_type": "unknown"
        },
        "to": {
            "address": "b3fe1649862d7889ab002e0224a2db54870eafa9",
            "owner_type": "unknown"
        },
        "timestamp": 1588578025,
        "amount": 500000,
        "amount_usd": 503430.84,
        "transaction_count": 1
    }, {
        "blockchain": "ethereum",
        "symbol": "USDT",
        "id": "655553158",
        "transaction_type": "transfer",
        "hash": "19a393cb0fe2cd5975a3741e43f05859877b639b1c93dd19acd4abfa08715530",
        "from": {
            "address": "df38a19aa5db1f15c6df389d86175285d45fa572",
            "owner_type": "exchange",
            "owner": "stuart"
        },
        "to": {
            "address": "80c6e081ae5813b163357774003d3695faa0f53e",
            "owner_type": "exchange",
            "owner": "stuart"
        },
        "timestamp": 1588578065,
        "amount": 500000,
        "amount_usd": 509513.7,
        "transaction_count": 1
    }]
}
text_success_bad_count = {
    "result":
    "success",
    "cursor":
    "2712f286-2712f286-5eafc711",
    "count":
    3,
    "transactions": [{
        "blockchain": "ethereum",
        "symbol": "usdt",
        "id": "655552612",
        "transaction_type": "transfer",
        "hash": "4cdfc57c737b4214fbce384e57f50d8b52f80c2eb470654f9fdc2062c534bf42",
        "from": {
            "address": "477b8d5ef7c2c42db84deb555419cd817c336b6f",
            "owner_type": "unknown"
        },
        "to": {
            "address": "b3fe1649862d7889ab002e0224a2db54870eafa9",
            "owner_type": "unknown"
        },
        "timestamp": 1588578025,
        "amount": 500000,
        "amount_usd": 503430.84,
        "transaction_count": 1
    }, {
        "blockchain": "ethereum",
        "symbol": "usdt",
        "id": "655553158",
        "transaction_type": "transfer",
        "hash": "19a393cb0fe2cd5975a3741e43f05859877b639b1c93dd19acd4abfa08715530",
        "from": {
            "address": "df38a19aa5db1f15c6df389d86175285d45fa572",
            "owner_type": "unknown"
        },
        "to": {
            "address": "80c6e081ae5813b163357774003d3695faa0f53e",
            "owner_type": "unknown"
        },
        "timestamp": 1588578065,
        "amount": 500000,
        "amount_usd": 509513.7,
        "transaction_count": 1
    }]
}
text_success_bad_key = {
    "result":
    "success",
    "cursor":
    "2712f286-2712f286-5eafc711",
    "count":
    2,
    "transactions": [{
        "bad_key": "ethereum",
        "symbol": "usdt",
        "id": "655552612",
        "transaction_type": "transfer",
        "hash": "4cdfc57c737b4214fbce384e57f50d8b52f80c2eb470654f9fdc2062c534bf42",
        "from": {
            "address": "477b8d5ef7c2c42db84deb555419cd817c336b6f",
            "owner_type": "unknown"
        },
        "to": {
            "address": "b3fe1649862d7889ab002e0224a2db54870eafa9",
            "owner_type": "unknown"
        },
        "timestamp": 1588578025,
        "amount": 500000,
        "amount_usd": 503430.84,
        "transaction_count": 1
    }, {
        "blockchain": "ethereum",
        "symbol": "usdt",
        "id": "655553158",
        "transaction_type": "transfer",
        "hash": "19a393cb0fe2cd5975a3741e43f05859877b639b1c93dd19acd4abfa08715530",
        "from": {
            "address": "df38a19aa5db1f15c6df389d86175285d45fa572",
            "owner_type": "unknown"
        },
        "to": {
            "address": "80c6e081ae5813b163357774003d3695faa0f53e",
            "owner_type": "unknown"
        },
        "timestamp": 1588578065,
        "amount": 500000,
        "amount_usd": 509513.7,
        "transaction_count": 1
    }]
}
text_bad_json = 'not a good json format'


class WhaleAlertAPI(unittest.TestCase):
    def setUp(self):
        self.transactions = Transactions()

    def test_correctly_formed_api_call_minimum_parameters(self):
        r = Response
        r.status_code = 200
        r.text = text_empty
        Session.get = mock.MagicMock().method()
        Session.get.return_value = (r)

        api_key = '123'
        start_time = 123456
        min_value = 100000
        end_time = None
        cursor = None
        limit = 100
        call_parameters = {}
        call_parameters['api_key'] = api_key
        call_parameters['start'] = start_time
        call_parameters['min_value'] = min_value
        call_parameters['limit'] = 100

        expected = [
            mock.call(settings.whale_get_transactions_url,
                      params=call_parameters,
                      timeout=settings.whale_call_timeout_seconds)
        ]
        self.transactions.get_transactions(start_time, end_time, api_key, cursor, min_value, limit)
        self.assertEqual(expected, Session.get.mock_calls)

    def test_correctly_formed_api_call_all_parameters(self):
        r = Response
        r.status_code = 200
        r.text = text_empty
        Session.get = mock.MagicMock().method()
        Session.get.return_value = (r)

        api_key = '123'
        start_time = 123456
        min_value = 100000
        end_time = 234567
        cursor = 'asdf'
        limit = 100
        call_parameters = {}
        call_parameters['api_key'] = api_key
        call_parameters['start'] = start_time
        call_parameters['min_value'] = min_value
        call_parameters['limit'] = 100
        call_parameters['end'] = end_time
        call_parameters['cursor'] = cursor

        expected = [
            mock.call(settings.whale_get_transactions_url,
                      params=call_parameters,
                      timeout=settings.whale_call_timeout_seconds)
        ]
        self.transactions.get_transactions(start_time, end_time, api_key, cursor, min_value, limit)
        self.assertEqual(expected, Session.get.mock_calls)

    def test_handle_connection_error_exception(self):
        Session.get = mock.MagicMock().method()
        Session.get.side_effect = ConnectionError
        time.sleep = mock.MagicMock()
        success, transactions, status = self.make_nomral_request()
        call_count = len(Session.get.call_args_list)
        self.assertEqual(call_count, settings.whale_retries_on_failure + 1)
        self.assertEqual(success, False)

    def test_handle_timeouterror_exception(self):
        Session.get = mock.MagicMock().method()
        Session.get.side_effect = Timeout
        time.sleep = mock.MagicMock()
        success, transactions, status = self.make_nomral_request()
        call_count = len(Session.get.call_args_list)
        self.assertEqual(call_count, settings.whale_retries_on_failure + 1)
        self.assertEqual(success, False)

    def test_handle_too_many_redirects_exception(self):
        Session.get = mock.MagicMock().method()
        Session.get.side_effect = TooManyRedirects
        time.sleep = mock.MagicMock()
        success, transactions, status = self.make_nomral_request()
        call_count = len(Session.get.call_args_list)
        self.assertEqual(call_count, settings.whale_retries_on_failure + 1)
        self.assertEqual(success, False)

    def test_handle_other_exception(self):
        Session.get = mock.MagicMock().method()
        Session.get.side_effect = ValueError
        time.sleep = mock.MagicMock()
        success, transactions, status = self.make_nomral_request()
        call_count = len(Session.get.call_args_list)
        self.assertEqual(call_count, settings.whale_retries_on_failure + 1)
        self.assertEqual(success, False)

    def test_bad_json_response_handled_ok(self):
        r = Response
        r.status_code = 200
        r.text = text_bad_json
        Session.get = mock.MagicMock().method()
        Session.get.return_value = (r)
        success, transactions, status = self.make_nomral_request()
        self.assertEqual(success, False)
        self.assertEqual(status[settings.status_file_option_error_code], 5)

    def test_parsing_error_response(self):
        r = Response
        r.status_code = 401
        r.text = json.dumps(text_error)
        Session.get = mock.MagicMock().method()
        Session.get.return_value = (r)
        success, transactions, status = self.make_nomral_request()
        self.assertEqual(success, False)
        self.assertEqual(status[settings.status_file_option_error_code], 401)

    def test_parsing_error_response_bad_key(self):
        r = Response
        r.status_code = 401
        r.text = json.dumps(text_error_bad_key)
        Session.get = mock.MagicMock().method()
        Session.get.return_value = (r)
        success, transactions, status = self.make_nomral_request()
        self.assertEqual(success, False)
        self.assertEqual(status[settings.status_file_option_error_code], 7)

    def test_parsing_good_response_no_transactions(self):
        r = Response
        r.status_code = 200
        r.text = json.dumps(text_empty)
        Session.get = mock.MagicMock().method()
        Session.get.return_value = (r)
        success, transactions, status = self.make_nomral_request()
        self.assertEqual(success, True)
        self.assertEqual(status[settings.status_file_option_error_code], 200)

    def test_parsing_good_response_no_transactions_bad_key(self):
        r = Response
        r.status_code = 200
        r.text = json.dumps(text_empty_bad_key)
        Session.get = mock.MagicMock().method()
        Session.get.return_value = (r)
        success, transactions, status = self.make_nomral_request()
        self.assertEqual(success, False)
        self.assertEqual(status[settings.status_file_option_error_code], 9)

    def test_parsing_good_response_with_transactions_wrong_count(self):
        r = Response
        r.status_code = 200
        r.text = json.dumps(text_success_bad_count)
        Session.get = mock.MagicMock().method()
        Session.get.return_value = (r)
        success, transactions, status = self.make_nomral_request()
        self.assertEqual(success, False)
        self.assertEqual(status[settings.status_file_option_error_code], 8)

    def test_parsing_good_response_with_transactions(self):
        r = Response
        r.status_code = 200
        r.text = json.dumps(text_success)
        Session.get = mock.MagicMock().method()
        Session.get.return_value = (r)
        success, transactions, status = self.make_nomral_request()
        self.assertEqual(success, True)
        self.assertEqual(status[settings.status_file_option_error_code], 200)
        self.assertGreaterEqual(self.transactions.get_last_timestamp(), int(time.time()) - 1)
        self.assertEqual(self.transactions.get_last_cursor(), text_success['cursor'])
        self.assertEqual(transactions[1], text_success['transactions'][1])

    def test_parsing_good_response_with_transactions_bad_key(self):
        r = Response
        r.status_code = 200
        r.text = json.dumps(text_success_bad_key)
        Session.get = mock.MagicMock().method()
        Session.get.return_value = (r)
        success, transactions, status = self.make_nomral_request()
        self.assertEqual(success, False)
        self.assertEqual(status[settings.status_file_option_error_code], 10)

    def test_bad_unknown_json_parse_error_handled(self):
        r = Response
        r.status_code = 200
        r.text = text_bad_json
        Session.get = mock.MagicMock().method()
        Session.get.return_value = (r)
        old_jsonload = json.loads
        json.loads = mock.MagicMock().method()
        json.loads.side_effect = ValueError
        success, transactions, status = self.make_nomral_request()
        self.assertEqual(success, False)
        self.assertEqual(status[settings.status_file_option_error_code], 6)
        json.loads = old_jsonload

    def make_nomral_request(self):
        api_key = '123'
        start_time = 123456
        min_value = 500000
        end_time = 234567
        cursor = 'asdf'
        limit = 100
        return self.transactions.get_transactions(start_time, end_time, api_key, cursor, min_value, limit)
