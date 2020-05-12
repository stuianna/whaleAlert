import logging
import pandas as pd
from configchecker import ConfigChecker
import whalealert.settings as settings

log = logging.getLogger(__name__)


class Writer():
    """ Puslishing Whale Alert API status and database results"""
    def __init__(self, status, database):
        self.__status = status
        self.__database = database
        self.__health_list = [1] * settings.health_list_length
        self.__last_written = []
        if status is not None:
            log.debug("Pulisher started with initial status {}".format(status.get_expectations()))

    def get_status_object(self):
        """ Return the status object used"""
        return self.__status

    def get_database(self):
        """Return the database object used"""
        return self.__database

    def write_transactions(self, transactions):
        """
        Write transactions to the dataabse

        Parameters:
        transactions (dict): Transactions returned by api.get_trasactions

        Returns:
        True: Transactions were written successfully
        False: An error occured, status written to logs.
        """
        if len(transactions) == 0:
            log.debug("Trying to write an empty list of transactions")
            return False

        for transaction in transactions:
            try:
                transaction = self.__squash_dictionary(transaction)
                self.__create_tables_as_needed(transaction)
            except KeyError:
                log.error("Key error parsing keys from transaction {}".format(transaction))
                return False
            except Exception as e:
                log.error("Exception {} when parsing keys from transaction {}".format(e, transaction))
                return False
            if self.__add_entries(transaction) is False:
                log.error("Failed to add entriy to database. Entry {}".format(transaction))
                return False
        return True

    def get_last_written(self):
        current_transactions = list(self.__last_written)
        self.__last_written.clear()
        return pd.DataFrame(current_transactions)

    def __add_entries(self, transaction):
        table_name = transaction[settings.database_table_identifier]
        if len(self.__last_written) < settings.maximum_stored_latest_transaction:
            self.__last_written.append(transaction)
        return self.__database.insert(table_name, transaction)

    def __squash_dictionary(self, transaction):
        new_dict = dict(transaction)
        new_dict[settings.database_column_from_address] = transaction['from']['address']
        new_dict[settings.database_column_from_owner] = transaction['from']['owner']
        new_dict[settings.database_column_from_owner_type] = transaction['from']['owner_type']
        new_dict[settings.database_column_to_address] = transaction['to']['address']
        new_dict[settings.database_column_to_owner] = transaction['to']['owner']
        new_dict[settings.database_column_to_owner_type] = transaction['to']['owner_type']

        new_dict.pop('from', None)
        new_dict.pop('to', None)
        return new_dict

    def __create_tables_as_needed(self, transaction):
        self.__database.create_table(transaction[settings.database_table_identifier], settings.database_columns)

    def write_status(self, status):
        """"
        Write the logger status to the status file

        Returns:
        True: The file was written successfully
        False: The file couldn't be written, error status written to logs
        """
        if type(self.__status) is not ConfigChecker:
            return False
        try:
            self.__update_all_time(status)
            self.__update_current(status)
            self.__update_good_call_stats(status)
            self.__update_bad_call_stats(status)
        except KeyError:
            log.error("Key error when trying to write status {}".format(status))
            return False

        if not self.__status.write_configuration_file():
            log.error("Failed to write status file")
            return False
        return True

    def __update_good_call_stats(self, status):
        if status[settings.status_file_option_error_code] != 200:
            return
        self.__status.set_value(settings.status_file_last_good_call_section_name, settings.status_file_option_timeStamp,
                                status[settings.status_file_option_timeStamp])
        self.__status.set_value(settings.status_file_last_good_call_section_name,
                                settings.status_file_option_transaction_count,
                                status[settings.status_file_option_transaction_count])

    def __update_bad_call_stats(self, status):
        if status[settings.status_file_option_error_code] == 200:
            return
        self.__status.set_value(settings.status_file_last_failed_secion_name, settings.status_file_option_timeStamp,
                                status[settings.status_file_option_timeStamp])
        self.__status.set_value(settings.status_file_last_failed_secion_name, settings.status_file_option_error_code,
                                status[settings.status_file_option_error_code])
        self.__status.set_value(settings.status_file_last_failed_secion_name, settings.status_file_option_error_message,
                                status[settings.status_file_option_error_message])

    def __update_all_time(self, status):
        if status[settings.status_file_option_error_code] == 200:
            self.__increment_value(settings.status_file_all_time_section_name,
                                   settings.status_file_option_successful_calls)
        else:
            self.__increment_value(settings.status_file_all_time_section_name, settings.status_file_option_failed_calls)

        self.__calculate_success_rate(settings.status_file_all_time_section_name)

    def __update_current(self, status):
        if status[settings.status_file_option_error_code] == 200:
            self.__increment_value(settings.status_file_current_session_section_name,
                                   settings.status_file_option_successful_calls)
            self.__calculate_health(True)
        else:
            self.__increment_value(settings.status_file_current_session_section_name,
                                   settings.status_file_option_failed_calls)
            self.__calculate_health(False)
        self.__calculate_success_rate(settings.status_file_current_session_section_name)
        return True

    def __calculate_success_rate(self, section):
        good_calls = self.__status.get_value(section, settings.status_file_option_successful_calls)
        bad_calls = self.__status.get_value(section, settings.status_file_option_failed_calls)
        percent = 100 * good_calls / (good_calls + bad_calls)
        self.__status.set_value(section, settings.status_file_option_success_rate, round(percent, 2))

    def __calculate_health(self, success):
        self.__health_list.append((int(success)))
        self.__health_list.pop(0)
        health = round((100 * sum(self.__health_list) / len(self.__health_list)), 1)
        self.__status.set_value(settings.status_file_current_session_section_name, settings.status_file_option_health,
                                health)

    def __increment_value(self, section, key):
        self.__status.set_value(section, key, self.__status.get_value(section, key) + 1)
