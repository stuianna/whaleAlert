import unittest
from unittest import mock
import time
import logging
import os
import datetime
import pandas as pd
import whalealert.settings as settings
from whalealert.publisher.writer import Writer
from whalealert.publisher.reader import Reader
from whalealert.whalealert import WhaleAlert

logging.disable(logging.CRITICAL)
TEST_WORKING_DIR = os.path.join('tests', 'test_working_directory')

successful_call_with_trans = {
    'timestamp': '2020-05-04T16:20:37.276101',
    'error_code': 200,
    'error_message': '',
    'transaction_count': 3
}

test_good_data = [{
    'blockchain': 'bitcoin',
    'symbol': 'BTC',
    'id': '662472177',
    'transaction_type': 'transfer',
    'hash': '8d5ae34805f70d0a412964dca4dbd3f48bc103700686035a61b293cb91fe750d',
    'from': {
        'address': 'f2103b01cd7957f3a9d9726bbb74c0ccd3f355d3',
        'owner': 'binance',
        'owner_type': 'exchange'
    },
    'to': {
        'address': '3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be',
        'owner': 'binance',
        'owner_type': 'exchange'
    },
    'timestamp': 1188874414,
    'amount': 3486673,
    'amount_usd': 3508660.2,
    'transaction_count': 1
}, {
    'blockchain': 'ethereum',
    'symbol': 'USDT',
    'id': '662472178',
    'transaction_type': 'transfer',
    'hash': '246fc938c61f3ce1c59ede4f4aca302f46a9f894a300313d8f6c6600613f8659',
    'from': {
        'address': 'c3df5dfd8c8806961be9d02bd0832ec2a01e3413',
        'owner': 'binance',
        'owner_type': 'exchange'
    },
    'to': {
        'address': '3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be',
        'owner': 'binance',
        'owner_type': 'exchange'
    },
    'timestamp': 1288874414,
    'amount': 500000,
    'amount_usd': 503153.03,
    'transaction_count': 1
}, {
    'blockchain': 'tron',
    'symbol': 'USDT',
    'id': '662472729',
    'transaction_type': 'sold',
    'hash': '55f5fa53fd9c1a8430d79248e45f130b6ac08892ecd68e54cc600228919058d0',
    'from': {
        'address': 'c5a8859c44ac8aa2169afacf45b87c08593bec10',
        'owner_type': 'unknown',
        'owner': ''
    },
    'to': {
        'address': '7286c758578a2457e9ba36d46893176582acefb5',
        'owner': 'binance',
        'owner_type': 'exchange'
    },
    'timestamp': 1388874451,
    'amount': 500000000,
    'amount_usd': 500000000.23,
    'transaction_count': 1
}, {
    'blockchain': 'neo',
    'symbol': 'NEO',
    'id': '662472747',
    'transaction_type': 'burn',
    'hash': '40d261b3c94b5c174c802e3d452bd3ad36a3ba6171cbae670d89137ec7a6932e',
    'from': {
        'address': 'b5cebb87ff1a48ca28abc25b4584ff5148d1808e',
        'owner_type': 'unknown',
        'owner': ''
    },
    'to': {
        'address': 'f4561c710ba450aab302ffc3557ee59bbce94ca6',
        'owner_type': 'unknown',
        'owner': ''
    },
    'timestamp': 1488874451,
    'amount': 1691976.5,
    'amount_usd': 16895205,
    'transaction_count': 1
}, {
    'blockchain': 'ethereum',
    'symbol': 'ETH',
    'id': '662472982',
    'transaction_type': 'transfer',
    'hash': '866bd80566a494ac83da9822110fdb81189eefc4024208becfdafd3d76f8d921',
    'from': {
        'address': '8cce0f304933a784026f85a14daadb0a33ab06cf',
        'owner_type': 'unknown',
        'owner': ''
    },
    'to': {
        'address': '159d563ee3928cfa2bd3631b39266271888fe882',
        'owner_type': 'unknown',
        'owner': ''
    },
    'timestamp': 1588874481,
    'amount': 500000.1,
    'amount_usd': 500000,
    'transaction_count': 1
}]

expected_pretty_output = '\x1b[33m{} \x1b[0m\x1b[37m500000.10 \x1b[31mETH\x1b[36m (500,000.00 USD) \x1b[0m transferred from \x1b[34munknown\x1b[0m to \x1b[34munknown\x1b[0m.'.format(
    Reader.to_local_time(test_good_data[4]['timestamp']))
expected_pretty_large_sum = '\x1b[33m{} \x1b[0m\x1b[37m1691976.50 \x1b[31mNEO\x1b[36m\x1b[1m (16,895,205.00 USD) \x1b[0m \x1b[31mburned\x1b[0m at \x1b[34munknown\x1b[0m.'.format(
    Reader.to_local_time(test_good_data[3]['timestamp']))
expected_pretty_huge_sum = '\x1b[33m{} \x1b[0m\x1b[37m500000000.00 \x1b[31mUSDT \x1b[36m\x1b[1m\x1b[4m(500,000,000.23 USD)\x1b[0m sold from \x1b[34munknown\x1b[0m to \x1b[34mbinance\x1b[0m.'.format(
    Reader.to_local_time(test_good_data[2]['timestamp']))


def cleanup_working_directories():
    try:
        os.remove(os.path.join(TEST_WORKING_DIR, settings.data_file_directory, settings.database_file_name))
        os.remove(os.path.join(TEST_WORKING_DIR, settings.data_file_directory, settings.status_file_name))
        os.remove(os.path.join(TEST_WORKING_DIR, settings.input_configuation_filename))
        os.removedirs(os.path.join(TEST_WORKING_DIR, settings.data_file_directory))
        os.removedirs(TEST_WORKING_DIR)
    except Exception as e_r:
        _ = e_r


def flattern_transactions(transactions):
    new_trans = []
    for t in transactions:
        new_dict = dict(t)
        new_dict[settings.database_column_from_address] = t['from']['address']
        new_dict[settings.database_column_from_owner] = t['from']['owner']
        new_dict[settings.database_column_from_owner_type] = t['from']['owner_type']
        new_dict[settings.database_column_to_address] = t['to']['address']
        new_dict[settings.database_column_to_owner] = t['to']['owner']
        new_dict[settings.database_column_to_owner_type] = t['to']['owner_type']

        new_dict.pop('from', None)
        new_dict.pop('to', None)
        new_trans.append(new_dict)
    return new_trans


def format_output(data, as_dict=False):
    if data['to']['owner'] == '':
        data['to']['owner'] = 'unknown'
    if data['from']['owner'] == '':
        data['from']['owner'] = 'unknown'
    if as_dict:
        return {
            'timestamp':
            Reader.to_local_time(data['timestamp']),
            'text':
            str("{:.2f}".format(data['amount'])) + " " + data['symbol'].upper() + " (" +
            Reader.format_currency(data['amount_usd']) + " USD) " + "transferred from " + data['from']['owner'] +
            ' to ' + data['to']['owner'] + '.'
        }

    else:
        return Reader.to_local_time(data['timestamp']) + " " + str("{:.2f}".format(
            data['amount'])) + " " + data['symbol'].upper() + " (" + Reader.format_currency(
                data['amount_usd']
            ) + " USD) " + "transferred from " + data['from']['owner'] + ' to ' + data['to']['owner'] + '.\n'


class RequestingStatusByExchange(unittest.TestCase):
    def setUp(self):
        self.whale = WhaleAlert(working_directory=TEST_WORKING_DIR)
        self.writer = Writer(self.whale.get_status(), self.whale.get_database())
        self.reader = Reader(self.whale.get_status(), self.whale.get_database())

    def tearDown(self):
        cleanup_working_directories()

    def add_call_to_database(self, data):
        self.writer.write_transactions(data)

    def test_single_blockchain_single_symbol_request_one_result(self):
        self.add_call_to_database(test_good_data)
        request = dict(settings.request_format)
        request[settings.request_blockchain] = ['bitcoin']
        request[settings.request_symbols] = ['BTC']
        request[settings.request_maximum_results] = 1
        request[settings.request_from_time] = 0
        data = test_good_data[0]
        expected_output = format_output(data)
        expected_output = expected_output[:-1]
        output = self.reader.data_request(request)
        self.assertEqual(output, expected_output)

    def test_single_blockchain_multiple_symbols_request_one_result(self):
        self.add_call_to_database(test_good_data)
        request = dict(settings.request_format)
        request[settings.request_blockchain] = ['ethereum']
        request[settings.request_symbols] = ['USDT', "ETH"]
        request[settings.request_maximum_results] = 1
        request[settings.request_from_time] = 0
        data = test_good_data[4]
        expected_output = format_output(data)
        expected_output = expected_output[:-1]
        output = self.reader.data_request(request)
        self.assertEqual(output, expected_output)

    def test_single_blockchain_multiple_symbols_request_multiple_results(self):
        self.add_call_to_database(test_good_data)
        request = dict(settings.request_format)
        request[settings.request_blockchain] = ['ethereum']
        request[settings.request_symbols] = ['USDT', "ETH"]
        request[settings.request_maximum_results] = 2
        request[settings.request_from_time] = 0
        data = test_good_data[1]
        expected_output = format_output(data)
        data = test_good_data[4]
        expected_output = expected_output + format_output(data)
        expected_output = expected_output[:-1]
        output = self.reader.data_request(request)
        self.assertEqual(output, expected_output)

    def test_multiple_blockchain_multiple_symbols_request_multiple_results(self):
        self.add_call_to_database(test_good_data)
        request = dict(settings.request_format)
        request[settings.request_blockchain] = ['ethereum', 'tron']
        request[settings.request_symbols] = ['USDT', "ETH"]
        request[settings.request_maximum_results] = 5
        request[settings.request_from_time] = 0
        data = test_good_data[1]
        expected_output = format_output(data)
        data = test_good_data[2]
        expected_output = expected_output + format_output(data)
        data = test_good_data[4]
        expected_output = expected_output + format_output(data)
        expected_output = expected_output[:-1]
        output = self.reader.data_request(request)
        self.assertEqual(output, expected_output)

    def test_multiple_blockchain_multiple_symbols_request_one_result(self):
        self.add_call_to_database(test_good_data)
        request = dict(settings.request_format)
        request[settings.request_blockchain] = ['ethereum', 'tron']
        request[settings.request_symbols] = ['USDT', "ETH"]
        request[settings.request_maximum_results] = 1
        request[settings.request_from_time] = 0
        data = test_good_data[4]
        expected_output = format_output(data)
        expected_output = expected_output[:-1]
        output = self.reader.data_request(request)
        self.assertEqual(output, expected_output)

    def test_invalid_blockchain_is_ignored(self):
        self.add_call_to_database(test_good_data)
        request = dict(settings.request_format)
        request[settings.request_blockchain] = ['ethereum', 'not_a_blockchain']
        request[settings.request_symbols] = ['USDT', "ETH"]
        request[settings.request_maximum_results] = 5
        request[settings.request_from_time] = 0
        data = test_good_data[1]
        expected_output = format_output(data)
        data = test_good_data[4]
        expected_output = expected_output + format_output(data)
        expected_output = expected_output[:-1]
        output = self.reader.data_request(request)
        self.assertEqual(output, expected_output)

    def test_invalid_symbols_are_ignored(self):
        self.add_call_to_database(test_good_data)
        request = dict(settings.request_format)
        request[settings.request_blockchain] = ['ethereum', 'tron']
        request[settings.request_symbols] = ["ETH"]
        request[settings.request_maximum_results] = 5
        request[settings.request_from_time] = 0
        data = test_good_data[4]
        expected_output = format_output(data)
        expected_output = expected_output[:-1]
        output = self.reader.data_request(request)
        self.assertEqual(output, expected_output)

    def test_values_only_taken_after_timestamp(self):
        self.add_call_to_database(test_good_data)
        request = dict(settings.request_format)
        request[settings.request_blockchain] = ['ethereum', 'tron']
        request[settings.request_symbols] = ['USDT', "ETH"]
        request[settings.request_maximum_results] = 5
        request[settings.request_from_time] = 1488874451
        data = test_good_data[4]
        expected_output = format_output(data)
        expected_output = expected_output[:-1]
        output = self.reader.data_request(request)
        self.assertEqual(output, expected_output)

    def test_blockchain_wildcard_gets_all_blockchain(self):
        self.add_call_to_database(test_good_data)
        request = dict(settings.request_format)
        request[settings.request_blockchain] = ['*']
        request[settings.request_symbols] = ['USDT']
        request[settings.request_maximum_results] = 5
        request[settings.request_from_time] = 0
        data = test_good_data[1]
        expected_output = format_output(data)
        data = test_good_data[2]
        expected_output = expected_output + format_output(data)
        expected_output = expected_output[:-1]
        output = self.reader.data_request(request)
        self.assertEqual(output, expected_output)

    def test_symbol_widcard_gets_all_symbols(self):
        self.add_call_to_database(test_good_data)
        request = dict(settings.request_format)
        request[settings.request_blockchain] = ['ethereum']
        request[settings.request_symbols] = ['*']
        request[settings.request_maximum_results] = 5
        request[settings.request_from_time] = 0
        data = test_good_data[1]
        expected_output = format_output(data)
        data = test_good_data[4]
        expected_output = expected_output + format_output(data)
        expected_output = expected_output[:-1]
        output = self.reader.data_request(request)
        self.assertEqual(output, expected_output)

    def test_both_wildcards_return_all_results(self):
        self.add_call_to_database(test_good_data)
        request = dict(settings.request_format)
        request[settings.request_blockchain] = ['*']
        request[settings.request_symbols] = ['*']
        request[settings.request_maximum_results] = 5
        request[settings.request_from_time] = 0
        data = test_good_data[0]
        expected_output = format_output(data)
        data = test_good_data[1]
        expected_output = expected_output + format_output(data)
        data = test_good_data[2]
        expected_output = expected_output + format_output(data)
        data = test_good_data[3]
        expected_output = expected_output + format_output(data)
        data = test_good_data[4]
        expected_output = expected_output + format_output(data)
        expected_output = expected_output[:-1]
        output = self.reader.data_request(request)
        self.assertEqual(output, expected_output)

    def test_both_wildcards_return_all_results_as_dict(self):
        self.add_call_to_database(test_good_data)
        request = dict(settings.request_format)
        request[settings.request_blockchain] = ['*']
        request[settings.request_symbols] = ['*']
        request[settings.request_maximum_results] = 1
        request[settings.request_from_time] = 0
        data = test_good_data[4]
        expected_output = format_output(data, as_dict=True)
        output = self.reader.data_request(request, as_dict=True)
        self.assertEqual(output, [expected_output])

    def test_single_result_pretty_format(self):
        self.add_call_to_database(test_good_data)
        request = dict(settings.request_format)
        request[settings.request_blockchain] = ['*']
        request[settings.request_symbols] = ['*']
        request[settings.request_maximum_results] = 1
        request[settings.request_from_time] = 0
        output = self.reader.data_request(request, pretty=True)
        self.assertEqual([output], [expected_pretty_output])

    def test_single_result_pretty_format_medium_sum(self):
        self.add_call_to_database(test_good_data)
        request = dict(settings.request_format)
        request[settings.request_blockchain] = ['neo']
        request[settings.request_symbols] = ['*']
        request[settings.request_maximum_results] = 1
        request[settings.request_from_time] = 0
        output = self.reader.data_request(request, pretty=True)
        self.assertEqual([output], [expected_pretty_large_sum])

    def test_single_pretty_format_huge_sum(self):
        self.add_call_to_database(test_good_data)
        request = dict(settings.request_format)
        request[settings.request_blockchain] = ['tron']
        request[settings.request_symbols] = ['*']
        request[settings.request_maximum_results] = 1
        request[settings.request_from_time] = 0
        output = self.reader.data_request(request, pretty=True)
        self.assertEqual([output], [expected_pretty_huge_sum])

    def test_calling_without_database_returns_empty_string(self):
        reader = Reader()
        request = dict(settings.request_format)
        request[settings.request_blockchain] = ['*']
        request[settings.request_symbols] = ['*']
        request[settings.request_maximum_results] = 5
        request[settings.request_from_time] = 0
        output = reader.data_request(request)
        self.assertEqual(output, '')

    def test_calling_with_empty_database_returns_empty_list(self):
        request = dict(settings.request_format)
        request[settings.request_blockchain] = ['*']
        request[settings.request_symbols] = ['*']
        request[settings.request_maximum_results] = 5
        request[settings.request_from_time] = 0
        output = self.reader.data_request(request, as_dict=True)
        self.assertEqual(output, [])

    def test_calling_with_empty_database_returns_empty_dataFrame(self):
        request = dict(settings.request_format)
        request[settings.request_blockchain] = ['*']
        request[settings.request_symbols] = ['*']
        request[settings.request_maximum_results] = 5
        request[settings.request_from_time] = 0
        output = self.reader.data_request(request, as_df=True)
        self.assertIs(output.empty, True)

    def test_bad_data_request_returns_empty_string(self):
        bad_request = {
            'bad_key': 'sfd',
            'another_bad_key': 'sfd',
        }
        output = self.reader.data_request(bad_request)
        self.assertEqual(output, '')

    def test_getting_all_data_as_df(self):
        self.add_call_to_database(test_good_data)
        request = dict(settings.request_format)
        request[settings.request_blockchain] = ['*']
        request[settings.request_symbols] = ['*']
        request[settings.request_maximum_results] = 5
        request[settings.request_from_time] = 0
        expected_output = pd.DataFrame(flattern_transactions(test_good_data))
        expected_output = expected_output.reindex(sorted(expected_output.columns), axis=1)
        output = self.reader.data_request(request, as_df=True)
        pd.testing.assert_frame_equal(expected_output, output)


class GettingLoggerStatus(unittest.TestCase):
    def setUp(self):
        self.whale = WhaleAlert(working_directory=TEST_WORKING_DIR)
        self.writer = Writer(self.whale.get_status(), self.whale.get_database())
        self.reader = Reader(self.whale.get_status(), self.whale.get_database(), self.whale.get_configuration())

    def tearDown(self):
        cleanup_working_directories()

    def write_good_status(self, unix_timestamp):
        status = dict()
        status['timestamp'] = Reader.to_local_time(unix_timestamp)
        status['error_code'] = 200
        status['error_message'] = 'A dud message'
        status['transaction_count'] = 0
        self.writer.write_status(status)

    def write_bad_status(self, unix_timestamp):
        status = dict()
        status['timestamp'] = Reader.to_local_time(unix_timestamp)
        status['error_code'] = 1
        status['error_message'] = 'A dud message'
        status['transaction_count'] = 0
        self.writer.write_status(status)

    def test_getting_status_stdout(self):
        last_good_call_seconds_ago = 300
        last_good_call_minutes = int(round(last_good_call_seconds_ago / 60, 0))
        health = round(100 * (settings.health_list_length - 1) / settings.health_list_length, 1)
        self.write_bad_status(int(time.time()) - 200)
        self.write_good_status(int(time.time()) - last_good_call_seconds_ago)
        output = self.reader.status_request()
        expected_std_status = "Last successful call {} minutes ago, health {}%".format(last_good_call_minutes, health)
        self.assertEqual(expected_std_status, output)

    def test_getting_status_dict(self):
        last_good_call_seconds_ago = 100
        last_good_call_minutes = int(round(last_good_call_seconds_ago / 60, 0))
        health = round(100 * (settings.health_list_length - 1) / settings.health_list_length, 1)
        self.write_bad_status(int(time.time()) - 200)
        self.write_good_status(int(time.time()) - last_good_call_seconds_ago)
        output = self.reader.status_request(as_dict=True)
        expected_status = {'last_call': last_good_call_minutes, 'health': health, 'status': 'Ok'}
        self.assertEqual(expected_status, output)

    def test_getting_status_dict_logger_not_ok(self):
        last_good_call_seconds_ago = 700
        last_good_call_minutes = int(round(last_good_call_seconds_ago / 60, 0))
        health = round(100 * (settings.health_list_length - 1) / settings.health_list_length, 1)
        self.write_bad_status(int(time.time()) - 200)
        self.write_good_status(int(time.time()) - last_good_call_seconds_ago)
        output = self.reader.status_request(as_dict=True)
        expected_status = {'last_call': last_good_call_minutes, 'health': health, 'status': 'Error'}
        self.assertEqual(expected_status, output)

    def test_request_status_with_no_working_directory_returns_none(self):
        reader = Reader()
        expected_status = None
        output = reader.status_request()
        self.assertEqual(expected_status, output)
