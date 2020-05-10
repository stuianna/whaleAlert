import unittest
from unittest import mock
import time
import logging
import os
import whalealert.settings as settings
from whalealert.publisher.writer import Writer
from whalealert.whalealert import WhaleAlert

logging.disable(logging.CRITICAL)
TEST_WORKING_DIR = os.path.join('tests', 'test_working_directory')
successful_call_with_trans = {
    'timestamp': '2020-05-04T16:20:37.276101',
    'error_code': 200,
    'error_message': '',
    'transaction_count': 3
}
successful_call_no_trans = {
    'timestamp': '2020-05-04T16:20:37.276101',
    'error_code': 200,
    'error_message': '',
    'transaction_count': 0
}
failed_call = {
    'timestamp': '2020-05-04T16:20:37.276101',
    'error_code': 401,
    'error_message': 'Bad API Key',
    'transaction_count': 0
}
bad_status = {'timestamp': '2020-05-04T16:20:37.276101'}
test_extra_key = [{
    'blockchain': 'bitcoin',
    'symbol': 'btc',
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
    'timestamp': 1588874414,
    'amount': 3486673,
    'amount_usd': 3508660.2,
    'transaction_count': 1,
    'extra_key': 1
}]

test_bad_key = [{
    'blockchain': 'bitcoin',
    'symbol': 'btc',
    'id': '662472177',
    'transaction_type': 'transfer',
    'hash': '8d5ae34805f70d0a412964dca4dbd3f48bc103700686035a61b293cb91fe750d',
    'from_a_bad_key': {
        'address': 'f2103b01cd7957f3a9d9726bbb74c0ccd3f355d3',
        'owner': 'binance',
        'owner_type': 'exchange'
    },
    'to': {
        'address': '3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be',
        'owner': 'binance',
        'owner_type': 'exchange'
    },
    'timestamp': 1588874414,
    'amount': 3486673,
    'amount_usd': 3508660.2,
    'transaction_count': 1,
    'extra_key': 1
}]

test_good_data = [{
    'blockchain': 'bitcoin',
    'symbol': 'btc',
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
    'timestamp': 1588874414,
    'amount': 3486673,
    'amount_usd': 3508660.2,
    'transaction_count': 1
}, {
    'blockchain': 'ethereum',
    'symbol': 'usdt',
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
    'timestamp': 1588874414,
    'amount': 500000,
    'amount_usd': 503153.03,
    'transaction_count': 1
}, {
    'blockchain': 'tron',
    'symbol': 'usdt',
    'id': '662472729',
    'transaction_type': 'transfer',
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
    'timestamp': 1588874451,
    'amount': 500000,
    'amount_usd': 500000,
    'transaction_count': 1
}, {
    'blockchain': 'neo',
    'symbol': 'neo',
    'id': '662472747',
    'transaction_type': 'transfer',
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
    'timestamp': 1588874451,
    'amount': 1691976.5,
    'amount_usd': 1689525,
    'transaction_count': 1
}, {
    'blockchain': 'ethereum',
    'symbol': 'usdc',
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
    'amount': 500000,
    'amount_usd': 500000,
    'transaction_count': 1
}]


def cleanup_working_directories():
    try:
        os.remove(os.path.join(TEST_WORKING_DIR, settings.data_file_directory, settings.database_file_name))
        os.remove(os.path.join(TEST_WORKING_DIR, settings.data_file_directory, settings.status_file_name))
        os.remove(os.path.join(TEST_WORKING_DIR, settings.input_configuation_filename))
        os.removedirs(os.path.join(TEST_WORKING_DIR, settings.data_file_directory))
        os.removedirs(TEST_WORKING_DIR)
    except Exception as e_r:
        _ = e_r


class WritingCurrentAndAllTimeStatus(unittest.TestCase):
    def setUp(self):
        self.whale = WhaleAlert(working_directory=TEST_WORKING_DIR)
        self.writer = Writer(self.whale.get_status(), self.whale.get_database())

    def tearDown(self):
        cleanup_working_directories()

    def test_writing_status_with_no_working_directory_handled_ok(self):
        writer = Writer(self.whale.get_status(), self.whale.get_database())
        writer.write_status(successful_call_no_trans)

    def test_writing_a_successful_call_updates_success_no_trans(self):
        previous_value_all_time = self.get_status_value(settings.status_file_all_time_section_name,
                                                        settings.status_file_option_successful_calls)
        previous_value_current = self.get_status_value(settings.status_file_current_session_section_name,
                                                       settings.status_file_option_successful_calls)
        success = self.writer.write_status(successful_call_no_trans)
        self.reload_status()
        new_value_all_time = self.get_status_value(settings.status_file_all_time_section_name,
                                                   settings.status_file_option_successful_calls)
        new_value_current = self.get_status_value(settings.status_file_current_session_section_name,
                                                  settings.status_file_option_successful_calls)
        self.assertEqual(success, True)
        self.assertEqual(new_value_all_time, previous_value_all_time + 1)
        self.assertEqual(new_value_current, previous_value_current + 1)

    def test_writing_a_successful_call_updates_success_with_trans(self):
        previous_value_all_time = self.get_status_value(settings.status_file_all_time_section_name,
                                                        settings.status_file_option_successful_calls)
        previous_value_current = self.get_status_value(settings.status_file_current_session_section_name,
                                                       settings.status_file_option_successful_calls)
        success = self.writer.write_status(successful_call_with_trans)
        self.reload_status()
        new_value_all_time = self.get_status_value(settings.status_file_all_time_section_name,
                                                   settings.status_file_option_successful_calls)
        new_value_current = self.get_status_value(settings.status_file_current_session_section_name,
                                                  settings.status_file_option_successful_calls)
        self.assertEqual(success, True)
        self.assertEqual(new_value_all_time, previous_value_all_time + 1)
        self.assertEqual(new_value_current, previous_value_current + 1)

    def test_writing_a_successful_call_doesnt_change_failed_calls(self):
        previous_value_all_time = self.get_status_value(settings.status_file_all_time_section_name,
                                                        settings.status_file_option_failed_calls)
        previous_value_current = self.get_status_value(settings.status_file_current_session_section_name,
                                                       settings.status_file_option_failed_calls)
        success = self.writer.write_status(successful_call_no_trans)
        self.reload_status()
        new_value_all_time = self.get_status_value(settings.status_file_all_time_section_name,
                                                   settings.status_file_option_failed_calls)
        new_value_current = self.get_status_value(settings.status_file_current_session_section_name,
                                                  settings.status_file_option_failed_calls)
        self.assertEqual(success, True)
        self.assertEqual(new_value_all_time, previous_value_all_time)
        self.assertEqual(new_value_current, previous_value_current)

    def test_writing_a_successful_call_doesnt_change_failed_calls_with_trans(self):
        previous_value_all_time = self.get_status_value(settings.status_file_all_time_section_name,
                                                        settings.status_file_option_failed_calls)
        previous_value_current = self.get_status_value(settings.status_file_current_session_section_name,
                                                       settings.status_file_option_failed_calls)
        success = self.writer.write_status(successful_call_with_trans)
        self.reload_status()
        new_value_all_time = self.get_status_value(settings.status_file_all_time_section_name,
                                                   settings.status_file_option_failed_calls)
        new_value_current = self.get_status_value(settings.status_file_current_session_section_name,
                                                  settings.status_file_option_failed_calls)
        self.assertEqual(success, True)
        self.assertEqual(new_value_all_time, previous_value_all_time)
        self.assertEqual(new_value_current, previous_value_current)

    def test_writing_a_failed_call_updates_failed(self):
        previous_value_all_time = self.get_status_value(settings.status_file_all_time_section_name,
                                                        settings.status_file_option_failed_calls)
        previous_value_current = self.get_status_value(settings.status_file_current_session_section_name,
                                                       settings.status_file_option_failed_calls)
        success = self.writer.write_status(failed_call)
        self.reload_status()
        new_value_all_time = self.get_status_value(settings.status_file_all_time_section_name,
                                                   settings.status_file_option_failed_calls)
        new_value_current = self.get_status_value(settings.status_file_current_session_section_name,
                                                  settings.status_file_option_failed_calls)
        self.assertEqual(success, True)
        self.assertEqual(new_value_all_time, previous_value_all_time + 1)
        self.assertEqual(new_value_current, previous_value_current + 1)

    def test_writing_a_failed_call_doesnt_change_successful_calls(self):
        previous_value_all_time = self.get_status_value(settings.status_file_all_time_section_name,
                                                        settings.status_file_option_successful_calls)
        previous_value_current = self.get_status_value(settings.status_file_current_session_section_name,
                                                       settings.status_file_option_successful_calls)
        success = self.writer.write_status(failed_call)
        self.reload_status()
        new_value_all_time = self.get_status_value(settings.status_file_all_time_section_name,
                                                   settings.status_file_option_successful_calls)
        new_value_current = self.get_status_value(settings.status_file_current_session_section_name,
                                                  settings.status_file_option_successful_calls)
        self.assertEqual(success, True)
        self.assertEqual(new_value_all_time, previous_value_all_time)
        self.assertEqual(new_value_current, previous_value_current)

    def test_writing_failed_and_successfull_calls_calculates_percent(self):
        self.writer.get_status_object().set_value(settings.status_file_all_time_section_name,
                                                  settings.status_file_option_success_rate, 0)
        self.writer.get_status_object().set_value(settings.status_file_current_session_section_name,
                                                  settings.status_file_option_success_rate, 0)
        self.writer.write_status(successful_call_no_trans)
        self.writer.write_status(successful_call_no_trans)
        self.writer.write_status(successful_call_no_trans)
        self.writer.write_status(failed_call)
        success = self.writer.write_status(failed_call)
        self.reload_status()
        percent_all_time = self.get_status_value(settings.status_file_all_time_section_name,
                                                 settings.status_file_option_success_rate)
        percent_current = self.get_status_value(settings.status_file_current_session_section_name,
                                                settings.status_file_option_success_rate)
        self.assertEqual(percent_all_time, 60.00)
        self.assertEqual(percent_current, 60.00)
        self.assertEqual(success, True)

    def test_writing_health(self):

        health_length = settings.health_list_length
        self.assertGreater(health_length, 10)
        self.writer.write_status(failed_call)
        success = self.writer.write_status(failed_call)
        expected_health = round(100 * (health_length - 2) / health_length, 1)
        self.reload_status()
        current_health = self.get_status_value(settings.status_file_current_session_section_name,
                                               settings.status_file_option_health)
        self.assertEqual(current_health, expected_health)
        self.assertEqual(success, True)

    def reload_status(self):
        target_file = os.path.join(TEST_WORKING_DIR, settings.data_file_directory, settings.status_file_name)
        self.writer.get_status_object().set_configuration_file(target_file)

    def get_status_value(self, section, key):
        return self.writer.get_status_object().get_value(section, key)


class WrintingLastCallStats(unittest.TestCase):
    def setUp(self):
        self.whale = WhaleAlert(working_directory=TEST_WORKING_DIR)
        self.writer = Writer(self.whale.get_status(), self.whale.get_database())

    def tearDown(self):
        cleanup_working_directories()

    def reload_status(self):
        target_file = os.path.join(TEST_WORKING_DIR, settings.data_file_directory, settings.status_file_name)
        self.writer.get_status_object().set_configuration_file(target_file)

    def get_status_value(self, section, key):
        return self.writer.get_status_object().get_value(section, key)

    def test_successful_call_writen_ok(self):
        status = successful_call_with_trans
        success = self.writer.write_status(status)
        self.reload_status()
        self.assertEqual(
            self.get_status_value(settings.status_file_last_good_call_section_name,
                                  settings.status_file_option_timeStamp), successful_call_with_trans['timestamp'])
        self.assertEqual(
            self.get_status_value(settings.status_file_last_good_call_section_name,
                                  settings.status_file_option_transaction_count),
            successful_call_with_trans['transaction_count'])
        self.assertEqual(success, True)

    def test_error_call_writen_ok(self):
        status = failed_call
        success = self.writer.write_status(status)
        self.reload_status()
        self.assertEqual(
            self.get_status_value(settings.status_file_last_failed_secion_name, settings.status_file_option_timeStamp),
            failed_call['timestamp'])
        self.assertEqual(
            self.get_status_value(settings.status_file_last_failed_secion_name, settings.status_file_option_error_code),
            failed_call['error_code'])
        self.assertEqual(
            self.get_status_value(settings.status_file_last_failed_secion_name,
                                  settings.status_file_option_error_message), failed_call['error_message'])
        self.assertEqual(success, True)


class HandlingErrors(unittest.TestCase):
    def setUp(self):
        self.whale = WhaleAlert(working_directory=TEST_WORKING_DIR)
        self.writer = Writer(self.whale.get_status(), self.whale.get_database())

    def tearDown(self):
        cleanup_working_directories()

    def test_status_key_error(self):
        success = self.writer.write_status(bad_status)
        self.assertIs(success, False)

    def test_status_handle_missing_status_file(self):
        cleanup_working_directories()
        success = self.writer.write_status(successful_call_with_trans)
        self.assertIs(success, False)

    def test_handle_bad_type(self):
        writer = Writer(None, None)
        success = writer.write_status(successful_call_with_trans)
        self.assertIs(success, False)


class WritingData(unittest.TestCase):
    def setUp(self):
        self.whale = WhaleAlert(working_directory=TEST_WORKING_DIR)
        self.writer = Writer(self.whale.get_status(), self.whale.get_database())

    def tearDown(self):
        cleanup_working_directories()

    def test_writing_new_data_adds_tables_to_database(self):
        transactions = test_good_data
        success = self.writer.write_transactions(transactions)
        database = self.writer.get_database()
        tables = database.get_table_names()
        expected_tables = ['bitcoin', 'ethereum', 'tron', 'neo']
        self.assertEqual(success, True)
        self.assertEqual(tables, expected_tables)

    def test_writing_new_data_adds_correct_columns_to_table(self):
        transactions = test_good_data
        success = self.writer.write_transactions(transactions)
        database = self.writer.get_database()
        columns = database.get_column_names('bitcoin')
        expected_columns = sorted(list(settings.database_columns.keys()))
        self.assertEqual(success, True)
        self.assertEqual(expected_columns, columns)

    def test_writing_new_data_last_time_entry_is_correct(self):
        transactions = test_good_data
        success = self.writer.write_transactions(transactions)
        database = self.writer.get_database()
        last_entry = database.get_last_time_entry('bitcoin')
        expected_entry = {
            'blockchain': 'bitcoin',
            'symbol': 'btc',
            'id': '662472177',
            'transaction_type': 'transfer',
            'hash': '8d5ae34805f70d0a412964dca4dbd3f48bc103700686035a61b293cb91fe750d',
            'from_address': 'f2103b01cd7957f3a9d9726bbb74c0ccd3f355d3',
            'from_owner': 'binance',
            'from_owner_type': 'exchange',
            'to_address': '3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be',
            'to_owner': 'binance',
            'to_owner_type': 'exchange',
            'timestamp': 1588874414,
            'amount': 3486673,
            'amount_usd': 3508660.2,
            'transaction_count': 1
        }
        self.assertEqual(success, True)
        self.assertEqual(expected_entry, last_entry)

    def test_writing_new_data_extra_key_returns_false(self):
        transaction = test_extra_key
        success = self.writer.write_transactions(transaction)
        self.assertEqual(success, False)

    def test_writing_empty_transactions_returns_false(self):
        transactions = []
        success = self.writer.write_transactions(transactions)
        self.assertEqual(success, False)

    def test_writing_with_a_bad_key_returns_false(self):
        transactions = test_bad_key
        success = self.writer.write_transactions(transactions)
        self.assertEqual(success, False)

    def test_writing_with_a_bad_dictionary_returns_false(self):
        transactions = dict(test_bad_key[0])
        success = self.writer.write_transactions(transactions)
        self.assertEqual(success, False)

    def test_writing_successive_entries(self):
        transactions = test_good_data
        success = self.writer.write_transactions(transactions)
        success = self.writer.write_transactions(transactions)
        success = self.writer.write_transactions(transactions)
        database = self.writer.get_database()
        df = database.table_to_df('bitcoin')
        self.assertEqual(len(df), 3)

        # There are two ethereum transaction in the good data
        df = database.table_to_df('ethereum')
        self.assertEqual(len(df), 6)

        self.assertEqual(success, True)

    def test_writing_wrong_data_type(self):
        transactions = 'A string'
        success = self.writer.write_transactions(transactions)
        self.assertEqual(success, False)
