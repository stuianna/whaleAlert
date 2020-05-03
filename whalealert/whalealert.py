import logging
import os
import sys
from configchecker import ConfigChecker
from dbops.sqhelper import SQHelper
from whalealert.api.transactions import Transactions
import whalealert.settings as settings

log = logging.getLogger(__name__)

class WhaleAlert():
    """ Python wrapper for the Whale Watch API"""

    def __init__(self, working_directory=None, log_level=logging.WARNING):
        if working_directory is not None:
            self.__make_directories_as_needed(working_directory)
            self.__setup_logging(working_directory, log_level)
            self.__config = self.__generate_configuration(working_directory)
            self.__database = self.__setup_database(working_directory)
            self.__status = self.__setup_status_file(working_directory)
        else:
            self.__config = None
            self.__status = None
            self.__database = None
        log.debug("Started new Whale Alert API wrapper.")
        self.transactions = Transactions()

    def __setup_logging(self, working_directory, log_level):
        logging_file = os.path.join(working_directory, settings.data_file_directory, settings.log_file_name)
        try:
            logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                                datefmt='%m/%d/%Y %I:%M:%S%p', level=logging.DEBUG, filename=logging_file)
        except Exception as e_r:
            print("Failed to create logging file. Exception '{}'".format(e_r), file=sys.stderr)
            raise

    def __setup_status_file(self, working_directory):
        status = ConfigChecker();
        status.set_expectation(settings.status_file_last_good_call_section_name, settings.status_file_option_timeStamp, str, '')

        status.set_expectation(settings.status_file_last_failed_secion_name, settings.status_file_option_timeStamp, str, '')
        status.set_expectation(settings.status_file_last_failed_secion_name, settings.status_file_option_error_code, int, 0)
        status.set_expectation(settings.status_file_last_failed_secion_name, settings.status_file_option_error_message, str, '')

        status.set_expectation(settings.status_file_current_session_section_name, settings.status_file_option_successful_calls, int, 0)
        status.set_expectation(settings.status_file_current_session_section_name, settings.status_file_option_failed_calls, int, 0)
        status.set_expectation(settings.status_file_current_session_section_name, settings.status_file_option_success_rate, float, 0.0)
        status.set_expectation(settings.status_file_current_session_section_name, settings.status_file_option_health, float, 100.0)

        status.set_expectation(settings.status_file_all_time_section_name, settings.status_file_option_successful_calls, int, 0)
        status.set_expectation(settings.status_file_all_time_section_name, settings.status_file_option_failed_calls, int, 0)
        status.set_expectation(settings.status_file_all_time_section_name, settings.status_file_option_success_rate, float, 0.0)

        target_file = os.path.join(working_directory, settings.data_file_directory, settings.status_file_name)
        status.set_configuration_file(target_file)
        status.write_configuration_file(target_file)
        return status

    def __setup_database(self, working_directory):
        file_location = os.path.join(working_directory,
                                     settings.data_file_directory,
                                     settings.database_file_name)
        database = SQHelper(file_location)
        if not database.exists():
            log.critical("Failed to create required database file, exiting")
            raise
        return database

    def __generate_configuration(self, working_directory):
        self.__make_directories_as_needed(working_directory)

        config = ConfigChecker()
        config.set_expectation(settings.API_section_name, settings.API_option_private_key, str, settings.API_option_privatate_key_default)
        config.set_expectation(settings.API_section_name, settings.API_option_interval, int, settings.API_option_interval_default)
        config.set_expectation(settings.API_section_name, settings.API_option_minimum_value, int, settings.API_option_minimum_value_default)

        target_directory = os.path.join(working_directory, settings.input_configuation_filename)
        config.set_configuration_file(target_directory)
        config.write_configuration_file(target_directory)
        return config

    def __make_directories_as_needed(self, working_directory):
        target_directory = os.path.join(working_directory, settings.data_file_directory)
        self.__make_dir(target_directory)

    def __make_dir(self, target_directory):
        if not os.path.exists(target_directory):
            try:
                log.debug("Creating new directory '{}'".format(target_directory))
                os.makedirs(target_directory)
            except OSError as e_r:
                log.error("Cannot create directory '{}'. Exception '{}'".format(target_directory, e_r))
                raise

    def get_configuration(self):
        """ Get the configuration used

        Note: This function always returns None if a working_directory is not supplied when the class object is created.

        Returns:
        config (ConfigChecker) if a valid configuration exists.
        None: No configuration exists
        """
        return self.__config

    def get_status(self):
        """ Get the status file used

        Note: This function always returns None if a working_directory is not supplied when the class object is created.

        Returns:
        status (ConfigChecker) if a valid status file exists.
        None: No configuration exists
        """
        return self.__status

    def get_database(self):
        """ Get the database file used

        Note: This function always returns None if a working_directory is not supplied when the class object is created.

        Returns:
        database (SQHelper) if a valid database is connected.
        None: No database is connected.

        """
        return self.__database

    def get_transactions(self, start_time, end_time=None, api_key=None, cursor=None, min_value=500000, limit=100):
        """ Use the Whale Alert API to get the lastest transactions for a given time period

        """
        if self.__config is None and api_key is None:
            raise ValueError("An API key needs to be supplied to get latest transactions")
        if self.__config is not None and api_key is None:
            api_key = self.__config.get_value(settings.API_section_name, settings.API_option_private_key)
        if self.__config is not None and min_value == 500000:
            min_value = self.__config.get_value(settings.API_section_name, settings.API_option_minimum_value)

        success, transactions, status = self.transactions.get_transactions(start_time, end_time, api_key, cursor, min_value, limit)
        return success, transactions, status

    def write_custom_status(self, status):
        pass

    def fetch_and_store_data(self, api_key=None):
        pass

    def to_excel(self, output_file='whaleAlert.xlsl'):
        pass

    def start_daemon(self):
        pass

    def data_request(self, request):
        pass

