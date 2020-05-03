import unittest
from unittest import mock
import logging
import os
from requests.models import Response
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import whalealert.settings as settings
from whalealert.whalealert import WhaleAlert
import json
import datetime

TEST_WORKING_DIR = os.path.join('tests', 'test_working_directory')
TEST_WORKING_DIR_BAD_PERMISSIONS = "/root/test"
TEST_WORKING_DIR_ALREADY_EXISTS = "tests/test_whale_alert.py"

class WhaleAlertInit(unittest.TestCase):
    """ Testing whale alert initialisation"""

    def setUp(self):
        self.whale = WhaleAlert(TEST_WORKING_DIR)
        self.config = self.whale.get_configuration()
        self.status = self.whale.get_status()
        self.database = self.whale.get_database()

    def tearDown(self):
        try:
            os.remove(os.path.join(TEST_WORKING_DIR, settings.data_file_directory, settings.database_file_name))
            os.remove(os.path.join(TEST_WORKING_DIR, settings.data_file_directory, settings.status_file_name))
            os.remove(os.path.join(TEST_WORKING_DIR, settings.input_configuation_filename))
            os.removedirs(os.path.join(TEST_WORKING_DIR, settings.data_file_directory))
            os.removedirs(TEST_WORKING_DIR)
        except Exception as e_r:
             _ = e_r

    def test_configuration_directories_and_files_created_ok_with_good_directory(self):
        whale = WhaleAlert(working_directory=TEST_WORKING_DIR)
        self.check_directories_are(TEST_WORKING_DIR, True)

    def test_configuration_directories_and_files_created_ok_with_bad_directory_permissions(self):
        self.assertRaises(PermissionError,WhaleAlert,TEST_WORKING_DIR_BAD_PERMISSIONS)

    def test_configuration_directories_and_files_created_ok_with_bad_directory_permissions(self):
        self.assertRaises(NotADirectoryError,WhaleAlert,TEST_WORKING_DIR_ALREADY_EXISTS)

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
        self.assertEqual(logs_exists, status)

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

