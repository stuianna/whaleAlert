import unittest
from unittest import mock
import logging
import os
from requests.models import Response
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import whalealert.settings as settings
from whalealert.whalealert import WhaleAlert
from whalealert.api.transactions import Transactions
import json
import datetime

TEST_WORKING_DIR = os.path.join('tests', 'test_working_directory')
TEST_WORKING_DIR_BAD_PERMISSIONS = "/root/test"
TEST_WORKING_DIR_ALREADY_EXISTS = "tests/test_whale_alert.py"

good_status = {
    'timestamp': '2020-05-04T16:20:37.276101',
    'error_code': 200,
    'error_message': '',
    'transaction_count': 3
}

bad_status = {
    'timestamp': '2020-05-04T16:20:37.276101',
    'error_code': 401,
    'error_message': 'Bad API Key',
    'transaction_count': 0
}

bad_formatted_status = {}

good_transactions = [{
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
}]

bad_transactions = [{
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
    'bad_key': 1,
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


class WhaleAlertInit(unittest.TestCase):
    """ Testing whale alert initialisation"""
    def setUp(self):
        self.whale = WhaleAlert(TEST_WORKING_DIR, log_level=logging.DEBUG)
        self.config = self.whale.get_configuration()
        self.status = self.whale.get_status()
        self.database = self.whale.get_database()

    def tearDown(self):
        cleanup_working_directories()

    def test_configuration_directories_and_files_created_ok_with_good_directory(self):
        whale = WhaleAlert(working_directory=TEST_WORKING_DIR, log_level=logging.DEBUG)
        self.check_directories_are(TEST_WORKING_DIR, True)

    def test_configuration_directories_and_files_created_ok_with_bad_directory_permissions(self):
        self.assertRaises(PermissionError, WhaleAlert, TEST_WORKING_DIR_BAD_PERMISSIONS, log_level=logging.DEBUG)

    def test_configuration_directories_and_files_created_ok_with_bad_directory_permissions(self):
        self.assertRaises(NotADirectoryError, WhaleAlert, TEST_WORKING_DIR_ALREADY_EXISTS, log_level=logging.DEBUG)

    def check_directories_are(self, directory, status):
        config_exists = os.path.exists(os.path.join(directory, settings.input_configuation_filename))
        data_dir_exists = os.path.exists(os.path.join(directory, settings.data_file_directory))
        database_exists = os.path.exists(
            os.path.join(directory, settings.data_file_directory, settings.database_file_name))
        status_exists = os.path.exists(os.path.join(directory, settings.data_file_directory, settings.status_file_name))
        logs_exists = os.path.exists(os.path.join(directory, settings.data_file_directory, settings.log_file_name))
        self.assertEqual(config_exists, status)
        self.assertEqual(data_dir_exists, status)
        self.assertEqual(database_exists, status)
        self.assertEqual(status_exists, status)

    def test_status_database_config_are_none_with_no_working_directory(self):
        whale = WhaleAlert()
        config = whale.get_configuration()
        status = whale.get_status()
        database = whale.get_database()
        self.assertIs(config, None)
        self.assertIs(status, None)
        self.assertIs(database, None)

    def test_config_values_are_default(self):
        self.assertEqual(self.config.get_value(settings.API_section_name, settings.API_option_private_key),
                         settings.API_option_privatate_key_default)
        self.assertEqual(self.config.get_value(settings.API_section_name, settings.API_option_interval),
                         settings.API_option_interval_default)
        self.assertEqual(self.config.get_value(settings.API_section_name, settings.API_option_minimum_value),
                         settings.API_option_minimum_value_default)
        self.assertEqual(self.config.get_value(settings.API_section_name, settings.API_option_historical_limit),
                         settings.API_option_historical_limit_default)

    def test_status_values_are_default(self):
        self.assertEqual(
            self.status.get_value(settings.status_file_last_good_call_section_name,
                                  settings.status_file_option_timeStamp), '')
        self.assertEqual(
            self.status.get_value(settings.status_file_last_good_call_section_name,
                                  settings.status_file_option_transaction_count), 0)

        self.assertEqual(
            self.status.get_value(settings.status_file_last_failed_secion_name, settings.status_file_option_timeStamp),
            '')
        self.assertEqual(
            self.status.get_value(settings.status_file_last_failed_secion_name, settings.status_file_option_error_code),
            0)
        self.assertEqual(
            self.status.get_value(settings.status_file_last_failed_secion_name,
                                  settings.status_file_option_error_message), '')

        self.assertEqual(
            self.status.get_value(settings.status_file_current_session_section_name,
                                  settings.status_file_option_successful_calls), 0)
        self.assertEqual(
            self.status.get_value(settings.status_file_current_session_section_name,
                                  settings.status_file_option_failed_calls), 0)
        self.assertEqual(
            self.status.get_value(settings.status_file_current_session_section_name,
                                  settings.status_file_option_success_rate), 0.0)
        self.assertEqual(
            self.status.get_value(settings.status_file_current_session_section_name,
                                  settings.status_file_option_health), 100.0)

        self.assertEqual(
            self.status.get_value(settings.status_file_all_time_section_name,
                                  settings.status_file_option_successful_calls), 0)
        self.assertEqual(
            self.status.get_value(settings.status_file_all_time_section_name, settings.status_file_option_failed_calls),
            0)
        self.assertEqual(
            self.status.get_value(settings.status_file_all_time_section_name, settings.status_file_option_success_rate),
            0.0)


class WhaleAlertAPICall(unittest.TestCase):
    """ Testing setup for whale alert api call"""
    def setUp(self):
        self.whale = WhaleAlert(TEST_WORKING_DIR)
        self.config = self.whale.get_configuration()
        self.status = self.whale.get_status()
        self.database = self.whale.get_database()

    def tearDown(self):
        cleanup_working_directories()

    def test_configuration_values_are_used_if_working_directory_supplied(self):
        self.whale.transactions.get_transactions = mock.MagicMock().method()
        self.whale.transactions.get_transactions.return_value = (False, {}, {})
        self.config.set_value(settings.API_section_name, settings.API_option_private_key, '1234')
        self.config.set_value(settings.API_section_name, settings.API_option_minimum_value, 10)
        expected = [mock.call(0, None, '1234', None, 10, 100)]
        self.whale.get_transactions(0)
        self.assertEqual(self.whale.transactions.get_transactions.mock_calls, expected)

    def test_configuration_values_are_overwrite_config_values_if_supplied(self):
        self.whale.transactions.get_transactions = mock.MagicMock().method()
        self.whale.transactions.get_transactions.return_value = (False, {}, {})
        self.config.set_value(settings.API_section_name, settings.API_option_private_key, '1234')
        self.config.set_value(settings.API_section_name, settings.API_option_minimum_value, 10)
        expected = [mock.call(0, None, '7890', None, 500, 100)]
        self.whale.get_transactions(0, api_key='7890', min_value=500)
        self.assertEqual(self.whale.transactions.get_transactions.mock_calls, expected)

    def test_no_config_value_raises_exception_if_api_key_not_supplied(self):
        whale = WhaleAlert()
        self.assertRaises(ValueError, whale.get_transactions, 0)

    def test_raises_exception_if_start_time_is_not_int(self):
        whale = WhaleAlert()
        self.assertRaises(ValueError, whale.get_transactions, 'not_an_int', api_key='1234')

    def test_raises_exception_if_end_time_is_not_int(self):
        whale = WhaleAlert()
        self.assertRaises(ValueError, whale.get_transactions, 0, end_time='not_an_int', api_key='1234')

    def test_no_config_get_transactions_works_as_normal(self):
        whale = WhaleAlert()
        whale.transactions.get_transactions = mock.MagicMock().method()
        whale.transactions.get_transactions.return_value = (False, {}, {})
        expected = [mock.call(0, None, 'asdf', None, 500000, 100)]
        whale.get_transactions(0, api_key='asdf')
        self.assertEqual(whale.transactions.get_transactions.mock_calls, expected)


class FetchAndStoreData(unittest.TestCase):
    def setUp(self):
        self.whale = WhaleAlert(TEST_WORKING_DIR)
        self.config = self.whale.get_configuration()
        self.status = self.whale.get_status()
        self.database = self.whale.get_database()

    def tearDown(self):
        cleanup_working_directories()

    def test_no_api_key_and_no_working_directory_returns_false_and_doesnt_call(self):
        whale = WhaleAlert()
        success = whale.fetch_and_store_data(0, 0)

        whale.transactions.get_transactions = mock.MagicMock().method()
        self.assertEqual(len(whale.transactions.get_transactions.mock_calls), 0)
        self.assertIs(success, False)

    def test_no_api_key_with_working_directory_calls_using_saved_api_key(self):
        self.config.set_value(settings.API_section_name, settings.API_option_private_key, 'zxcv')
        self.whale.transactions.get_transactions = mock.MagicMock().method()
        self.whale.transactions.get_transactions.return_value = (True, good_transactions, good_status)

        success = self.whale.fetch_and_store_data(0)

        expected = [mock.call(0, None, 'zxcv', None, 500000, 100)]
        self.assertEqual(self.whale.transactions.get_transactions.mock_calls, expected)
        self.assertIs(success, True)

    def test_supplying_api_key_with_working_directory_calls_using_supplied_api_key(self):
        self.config.set_value(settings.API_section_name, settings.API_option_private_key, 'zxcv')
        self.whale.transactions.get_transactions = mock.MagicMock().method()
        self.whale.transactions.get_transactions.return_value = (True, good_transactions, good_status)

        success = self.whale.fetch_and_store_data(0, api_key='poiu')

        expected = [mock.call(0, None, 'poiu', None, 500000, 100)]
        self.assertEqual(self.whale.transactions.get_transactions.mock_calls, expected)
        self.assertIs(success, True)

    def test_a_successful_call_causes_the_database_to_be_written(self):
        self.whale.transactions.get_transactions = mock.MagicMock().method()
        self.whale.transactions.get_transactions.return_value = (True, good_transactions, good_status)

        success = self.whale.fetch_and_store_data(0)
        database = self.whale.get_database()
        status = self.whale.get_status()

        successful_calls = status.get_value(settings.status_file_current_session_section_name,
                                            settings.status_file_option_successful_calls)
        failed_calls = status.get_value(settings.status_file_current_session_section_name,
                                        settings.status_file_option_failed_calls)

        df = database.table_to_df('bitcoin')
        self.assertEqual(len(df), 1)
        self.assertEqual(successful_calls, 1)
        self.assertEqual(failed_calls, 0)
        self.assertIs(success, True)

    def test_a_successful_call_with_failed_keys_causes_no_write_ands_a_failed_status(self):
        self.whale.transactions.get_transactions = mock.MagicMock().method()
        self.whale.transactions.get_transactions.return_value = (True, bad_transactions, good_status)

        success = self.whale.fetch_and_store_data(0)
        database = self.whale.get_database()
        status = self.whale.get_status()

        successful_calls = status.get_value(settings.status_file_current_session_section_name,
                                            settings.status_file_option_successful_calls)
        failed_calls = status.get_value(settings.status_file_current_session_section_name,
                                        settings.status_file_option_failed_calls)

        error_code = status.get_value(settings.status_file_last_failed_secion_name,
                                      settings.status_file_option_error_code)

        df = database.table_to_df('bitcoin')
        self.assertEqual(df.empty, True)
        self.assertEqual(successful_calls, 0)
        self.assertEqual(failed_calls, 1)
        self.assertIs(success, False)
        self.assertIs(error_code, 20)

    def test_a_failed_call_causes_no_write_to_database_and_failed_status(self):
        self.whale.transactions.get_transactions = mock.MagicMock().method()
        self.whale.transactions.get_transactions.return_value = (False, good_transactions, bad_status)

        success = self.whale.fetch_and_store_data(0)
        database = self.whale.get_database()
        status = self.whale.get_status()

        successful_calls = status.get_value(settings.status_file_current_session_section_name,
                                            settings.status_file_option_successful_calls)
        failed_calls = status.get_value(settings.status_file_current_session_section_name,
                                        settings.status_file_option_failed_calls)

        df = database.table_to_df('bitcoin')
        self.assertEqual(df, None)  # Nothing should have been written, so the table doesn't exist and none is returned
        self.assertEqual(successful_calls, 0)
        self.assertEqual(failed_calls, 1)
        self.assertIs(success, False)


class WritingCustomStatus(unittest.TestCase):
    def setUp(self):
        self.whale = WhaleAlert(TEST_WORKING_DIR)
        self.config = self.whale.get_configuration()
        self.status = self.whale.get_status()
        self.database = self.whale.get_database()

    def tearDown(self):
        cleanup_working_directories()

    def test_writing_well_formated_status_returns_true(self):
        success = self.whale.write_custom_status(good_status)
        self.assertEqual(success, True)

    def test_writing_badly_formated_status_returns_false(self):
        success = self.whale.write_custom_status(bad_formatted_status)
        self.assertEqual(success, False)

    def test_writing_status_with_no_working_directory_returns_false(self):
        whale = WhaleAlert()
        success = whale.write_custom_status(good_status)
        self.assertEqual(success, False)


class WritingExcelFile(unittest.TestCase):
    def setUp(self):
        self.whale = WhaleAlert(TEST_WORKING_DIR)
        self.config = self.whale.get_configuration()
        self.status = self.whale.get_status()
        self.database = self.whale.get_database()

    def tearDown(self):
        cleanup_working_directories()

    def test_return_false_if_no_working_directory(self):
        whale = WhaleAlert()
        success = whale.to_excel()
        self.assertEqual(success, False)

    def test_return_false_no_databases_exist(self):
        success = self.whale.to_excel()
        self.assertEqual(success, False)

    def test_writes_an_excel_file(self):
        self.whale.transactions.get_transactions = mock.MagicMock().method()
        self.whale.transactions.get_transactions.return_value = (True, good_transactions, good_status)
        success = self.whale.fetch_and_store_data(0)

        success = self.whale.to_excel()
        exists = os.path.exists('whaleAlert.xlsx')
        self.assertEqual(exists, True)
        self.assertEqual(success, True)
        os.remove("whaleAlert.xlsx")
