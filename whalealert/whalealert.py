import logging
import os
import sys
import socket
import subprocess
import time
import pandas as pd
from configchecker import ConfigChecker
from dbops.sqhelper import SQHelper
from whalealert.api.transactions import Transactions
from whalealert.publisher.writer import Writer
from whalealert.publisher.reader import Reader
import whalealert.settings as settings

log = logging.getLogger(__name__)
PROCESS_NAME = 'whaleAlertLogger'


def daemon_already_running():
    processName = PROCESS_NAME
    daemon_already_running._lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        daemon_already_running._lock_socket.bind('\0' + processName)
        log.info("New daemon logging instance started")
        return False
    except Exception as e:
        _ = e
        log.warning("Attempting to start daemon which is already running")
        return True


class WhaleAlert():
    """ Python wrapper for the Whale Watch API"""
    def __init__(self, working_directory=None, log_level=logging.WARNING):
        if working_directory is not None:
            self.__make_directories_as_needed(working_directory)
            self.__setup_logging(working_directory, log_level)
            self.__config = self.__generate_configuration(working_directory)
            self.__database = self.__setup_database(working_directory)
            self.__status = self.__setup_status_file(working_directory)
            self.__writer = Writer(self.__status, self.__database)
            self.__reader = Reader(self.__status, self.__database, self.__config)
            self.__last_data_request_time = int(time.time())
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
                                datefmt='%m/%d/%Y %I:%M:%S%p',
                                level=log_level,
                                filename=logging_file)
        except Exception as e_r:
            print("Failed to create logging file. Exception '{}'".format(e_r), file=sys.stderr)
            raise

    def __setup_status_file(self, working_directory):
        status = ConfigChecker()
        status.set_expectation(settings.status_file_last_good_call_section_name, settings.status_file_option_timeStamp,
                               str, '')
        status.set_expectation(settings.status_file_last_good_call_section_name,
                               settings.status_file_option_transaction_count, int, 0)

        status.set_expectation(settings.status_file_last_failed_secion_name, settings.status_file_option_timeStamp, str,
                               '')
        status.set_expectation(settings.status_file_last_failed_secion_name, settings.status_file_option_error_code,
                               int, 0)
        status.set_expectation(settings.status_file_last_failed_secion_name, settings.status_file_option_error_message,
                               str, '')

        status.set_expectation(settings.status_file_current_session_section_name,
                               settings.status_file_option_successful_calls, int, 0)
        status.set_expectation(settings.status_file_current_session_section_name,
                               settings.status_file_option_failed_calls, int, 0)
        status.set_expectation(settings.status_file_current_session_section_name,
                               settings.status_file_option_success_rate, float, 0.0)
        status.set_expectation(settings.status_file_current_session_section_name, settings.status_file_option_health,
                               float, 100.0)

        status.set_expectation(settings.status_file_all_time_section_name, settings.status_file_option_successful_calls,
                               int, 0)
        status.set_expectation(settings.status_file_all_time_section_name, settings.status_file_option_failed_calls,
                               int, 0)
        status.set_expectation(settings.status_file_all_time_section_name, settings.status_file_option_success_rate,
                               float, 0.0)

        target_file = os.path.join(working_directory, settings.data_file_directory, settings.status_file_name)
        status.set_configuration_file(target_file)
        status.write_configuration_file(target_file)
        return status

    def __setup_database(self, working_directory):
        file_location = os.path.join(working_directory, settings.data_file_directory, settings.database_file_name)
        database = SQHelper(file_location)
        if not database.exists():
            log.critical("Failed to create required database file, exiting")
            raise
        return database

    def __generate_configuration(self, working_directory):
        self.__make_directories_as_needed(working_directory)

        config = ConfigChecker()
        config.set_expectation(settings.API_section_name, settings.API_option_private_key, str,
                               settings.API_option_privatate_key_default)
        config.set_expectation(settings.API_section_name, settings.API_option_interval, int,
                               settings.API_option_interval_default)
        config.set_expectation(settings.API_section_name, settings.API_option_minimum_value, int,
                               settings.API_option_minimum_value_default)
        config.set_expectation(settings.API_section_name, settings.API_option_historical_limit, int,
                               settings.API_option_historical_limit_default)

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

        Parameters:
        start_time (int): A unix time stamp representing the start time to get transactions (exclusive)

        """

        if type(start_time) is not int:
            raise ValueError("Start time must be a unix time stamp integer")
        if end_time is not None and type(end_time) is not int:
            raise ValueError("End time must be a unix time stamp integer")
        if self.__config is None and api_key is None:
            raise ValueError("An API key needs to be supplied to get latest transactions")
        if self.__config is not None and api_key is None:
            api_key = self.__config.get_value(settings.API_section_name, settings.API_option_private_key)
        if self.__config is not None and min_value == 500000:
            min_value = self.__config.get_value(settings.API_section_name, settings.API_option_minimum_value)

        success, transactions, status = self.transactions.get_transactions(start_time, end_time, api_key, cursor,
                                                                           min_value, limit)
        return success, transactions, status

    def write_custom_status(self, status):
        """
        Write a custom status to the status file

        Parameters:
        status (dict) a python dictionary with four keys:
        - timestamp: An iso8601 timestamp
        - error_code: An integer error code. 200 represents success, other values are failures
        - error_message: A description of the error code
        - transaction_count: The number of transaction for this status (Leave at zero if not relevant)

        Returns:
        True: The status was written
        False: An error occured. Errors are sent to the logging module
        """
        if self.__status is None:
            return False
        return self.__writer.write_status(status)

    def fetch_and_store_data(self, start_time, end_time=None, api_key=None, cursor=None, min_value=500000, limit=100):
        if self.__database is None:
            log.error("Trying to fetch data without an API key or working directory (cannot store data).")
            return False
        elif self.__database is not None and api_key is None:
            api_key = self.__config.get_value(settings.API_section_name, settings.API_option_private_key)
            log.debug("Using configuration supplied API key")
        else:
            log.debug("Using overridden API key")

        success, transactions, status = self.transactions.get_transactions(start_time, end_time, api_key, cursor,
                                                                           min_value, limit)
        if success is True and len(transactions) > 0:
            written_ok = self.__writer.write_transactions(transactions)
            if written_ok is False:
                status['error_code'] = 20
                status['error_message'] = "Failed to write transactions to database"
                success = False
        elif success is True and len(transactions) == 0:
            success = False

        self.__writer.write_status(status)
        return success

    def start_daemon(self, force=False, print_output=False):
        if daemon_already_running() and force is False:
            return

        if self.__database is None:
            log.error("Trying to start daemon with no working directory")
            return

        api_key = self.__config.get_value(settings.API_section_name, settings.API_option_private_key)
        historical_limit = self.__config.get_value(settings.API_section_name, settings.API_option_historical_limit)
        request_interval = self.__config.get_value(settings.API_section_name, settings.API_option_interval)

        if request_interval <= 0:
            log.error("Request interval cannot be less than or equal to zero, daemon not starting")
            return
        if historical_limit <= 0:
            log.error("Historical limit cannot be less than or equal to zero, daemon not starting")
            return

        self.__status.set_value(settings.status_file_current_session_section_name,
                                settings.status_file_option_successful_calls, 0)
        self.__status.set_value(settings.status_file_current_session_section_name,
                                settings.status_file_option_failed_calls, 0)
        self.__status.set_value(settings.status_file_current_session_section_name,
                                settings.status_file_option_success_rate, 100.0)
        self.__status.set_value(settings.status_file_current_session_section_name, settings.status_file_option_health,
                                100.0)
        self.__status.write_configuration_file()

        while True:
            if self.transactions.get_last_cursor() is None:
                start_time = self.__find_latest_timestamp()
            else:
                start_time = 0

            end_time = int(time.time())
            if (end_time - start_time) > historical_limit:
                start_time = end_time - historical_limit

            success = self.fetch_and_store_data(start_time,
                                                end_time=end_time,
                                                api_key=api_key,
                                                cursor=self.transactions.get_last_cursor())

            if success is True and print_output:
                print(self.get_new_transaction(pretty=True))

            time.sleep(request_interval)

    def __find_latest_timestamp(self):
        tables = self.__database.get_table_names()
        latest_timestamp = 0
        for table in tables:
            last = self.__database.get_last_time_entry(table)
            try:
                if last['timestamp'] > latest_timestamp:
                    latest_timestamp = last['timestamp']
            except KeyError:
                pass
        if latest_timestamp >= time.time():
            latest_timestamp = time.time()
        return int(latest_timestamp)

    def kill():
        subprocess.Popen(['killall', PROCESS_NAME])

    def to_excel(self, output_file='whaleAlert.xlsx'):
        if self.__database is None:
            return False

        tables = self.__database.get_table_names()
        if len(tables) == 0:
            return False

        df_list = []
        for table in tables:
            df_list.append(self.__database.table_to_df(table))
        writer = pd.ExcelWriter(output_file, engine='openpyxl')
        _ = [A.to_excel(writer, sheet_name="{0}".format(tables[i])) for i, A in enumerate(df_list)]
        writer.save()
        return True

    def data_request(self,
                     start=0,
                     blockchain=None,
                     symbols=None,
                     max_results=20,
                     pretty=False,
                     as_df=False,
                     as_dict=False):

        request = dict(settings.request_format)
        if blockchain is not None:
            request[settings.request_blockchain] = blockchain
        else:
            request[settings.request_blockchain] = ['*']

        if symbols is not None:
            request[settings.request_symbols] = symbols
        else:
            request[settings.request_symbols] = ['*']

        request[settings.request_from_time] = start
        request[settings.request_maximum_results] = max_results
        return self.__reader.data_request(request, pretty, as_df, as_dict)

    def get_new_transaction(self, pretty=False, as_df=False, as_dict=False):
        """Get the transaction returned since the last call to this method

        WARNING: If start_daemon is called with print_output = True, then this method
        will not work as expected

        Parameters:
        pretty (Bool): Use ascii colour codes to format the output.
        as_df (Bool): Return all transactions as a dataframe
        as_dict (Bool): Retun as a {timestamp: '', 'text' ''} dictionary. Pretty output is also applied

        as_df takes precendence over as_dict.

        Returns:
        Formatted output depending on the passed parameters.
        """
        if as_df is True:
            return self.__writer.get_last_written()

        return self.__reader.dataframe_to_transaction_output(self.__writer.get_last_written(),
                                                             pretty=pretty,
                                                             as_dict=as_dict)

    def status_request(self, as_dict=False):
        return self.__reader.status_request(as_dict=as_dict)
