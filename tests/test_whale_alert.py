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
        self.assertRaises(PermissionError,WhaleAlert,TEST_WORKING_DIR_BAD_PERMISSIONS, log_level=logging.DEBUG)

    def test_configuration_directories_and_files_created_ok_with_bad_directory_permissions(self):
        self.assertRaises(NotADirectoryError,WhaleAlert,TEST_WORKING_DIR_ALREADY_EXISTS, log_level=logging.DEBUG)

    def check_directories_are(self, directory, status):
        config_exists = os.path.exists(os.path.join(directory, settings.input_configuation_filename))
        data_dir_exists = os.path.exists(os.path.join(directory, settings.data_file_directory))
        database_exists = os.path.exists(os.path.join(directory, settings.data_file_directory, settings.database_file_name))
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
        self.assertEqual(self.config.get_value(settings.API_section_name, settings.API_option_private_key), settings.API_option_privatate_key_default)
        self.assertEqual(self.config.get_value(settings.API_section_name, settings.API_option_interval), settings.API_option_interval_default)
        self.assertEqual(self.config.get_value(settings.API_section_name, settings.API_option_minimum_value), settings.API_option_minimum_value_default)

    def test_status_values_are_default(self):
        self.assertEqual(self.status.get_value(settings.status_file_last_good_call_section_name, settings.status_file_option_timeStamp), '')
        self.assertEqual(self.status.get_value(settings.status_file_last_good_call_section_name, settings.status_file_option_transaction_count), 0)

        self.assertEqual(self.status.get_value(settings.status_file_last_failed_secion_name, settings.status_file_option_timeStamp), '')
        self.assertEqual(self.status.get_value(settings.status_file_last_failed_secion_name, settings.status_file_option_error_code), 0)
        self.assertEqual(self.status.get_value(settings.status_file_last_failed_secion_name, settings.status_file_option_error_message), '')

        self.assertEqual(self.status.get_value(settings.status_file_current_session_section_name, settings.status_file_option_successful_calls), 0)
        self.assertEqual(self.status.get_value(settings.status_file_current_session_section_name, settings.status_file_option_failed_calls), 0)
        self.assertEqual(self.status.get_value(settings.status_file_current_session_section_name, settings.status_file_option_success_rate), 0.0)
        self.assertEqual(self.status.get_value(settings.status_file_current_session_section_name, settings.status_file_option_health), 100.0)

        self.assertEqual(self.status.get_value(settings.status_file_all_time_section_name, settings.status_file_option_successful_calls), 0)
        self.assertEqual(self.status.get_value(settings.status_file_all_time_section_name, settings.status_file_option_failed_calls), 0)
        self.assertEqual(self.status.get_value(settings.status_file_all_time_section_name, settings.status_file_option_success_rate), 0.0)

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
        self.whale.get_transactions(0,api_key='7890',min_value=500)
        self.assertEqual(self.whale.transactions.get_transactions.mock_calls, expected)

    def test_no_config_value_raises_exception_if_api_key_not_supplied(self):
        whale = WhaleAlert()
        self.assertRaises(ValueError,whale.get_transactions, 0)

    def test_raises_exception_if_start_time_is_not_int(self):
        whale = WhaleAlert()
        self.assertRaises(ValueError,whale.get_transactions, 'not_an_int', api_key='1234')

    def test_raises_exception_if_end_time_is_not_int(self):
        whale = WhaleAlert()
        self.assertRaises(ValueError,whale.get_transactions, 0, end_time='not_an_int', api_key='1234')

    def test_no_config_get_transactions_works_as_normal(self):
        whale = WhaleAlert()
        whale.transactions.get_transactions = mock.MagicMock().method()
        whale.transactions.get_transactions.return_value = (False, {}, {})
        expected = [mock.call(0, None, 'asdf', None, 500000, 100)]
        whale.get_transactions(0, api_key='asdf')
        self.assertEqual(whale.transactions.get_transactions.mock_calls, expected)
