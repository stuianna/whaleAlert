import logging
import time
import datetime
import pandas as pd
from colorama import Fore
from colorama import Style
import whalealert.settings as settings
from dateutil import tz, parser

log = logging.getLogger(__name__)
UNDERLINE = '\033[4m'


class Reader():
    """ Reading Whale Alert API status and database results"""
    def __init__(self, status=None, database=None, config=None):
        self.__status = status
        self.__database = database
        self.__config = config
        if status is not None:
            log.debug("Pulisher started with initial status {}".format(status.get_expectations()))

    def get_status_object(self):
        """ Return the status object used"""
        return self.__status

    def get_database(self):
        """Return the database object used"""
        return self.__database

    def status_request(self, as_dict=False):
        if self.__status is None or self.__config is None:
            return None

        if not self.__contains_valid_status():
            return None

        minutes = self.__calculate_minutes_since_last_good_call()
        health = self.__status.get_value(settings.status_file_current_session_section_name,
                                         settings.status_file_option_health)
        if as_dict:
            status = dict()
            if self.__logger_status_ok():
                status['status'] = "Ok"
            else:
                status['status'] = "Error"
            status['health'] = health
            status['last_call'] = minutes
            return status
        else:
            return "Last successful call {} minutes ago, health {}%".format(minutes, health)

    def __contains_valid_status(self):
        try:
            self.__config.get_value(settings.API_section_name, settings.API_option_interval)
            self.__status.get_value(settings.status_file_current_session_section_name,
                                    settings.status_file_option_health)
            Reader.from_local_time(
                self.__status.get_value(settings.status_file_last_good_call_section_name,
                                        settings.status_file_option_timeStamp))
            return True
        except Exception as e:
            log.error("Cannot request status, badly formed status file. Exception {}".format(e))
        return False

    def __logger_status_ok(self):
        call_inteval = self.__config.get_value(settings.API_section_name, settings.API_option_interval)
        last_call = Reader.from_local_time(
            self.__status.get_value(settings.status_file_last_good_call_section_name,
                                    settings.status_file_option_timeStamp))
        if (int(time.time()) - last_call) > (call_inteval * 5):
            return False
        return True

    def __calculate_minutes_since_last_good_call(self):
        lastCall = Reader.from_local_time(
            self.__status.get_value(settings.status_file_last_good_call_section_name,
                                    settings.status_file_option_timeStamp))
        currentTime = int(time.time())
        return int(round((currentTime - lastCall) / 60, 0))

    def data_request(self, request, pretty=False, as_df=False, as_dict=False):

        if self.get_database() is None:
            log.error("Requesting data from a database with no working directory")
            return self.__return_empty_result(pretty, as_df, as_dict)

        if self.__check_data_request_keys(request) is False:
            return self.__return_empty_result(pretty, as_df, as_dict)

        entries = self.__filter_request_by_blockchain(request)

        if len(entries) == 0:
            return self.__return_empty_result(pretty, as_df, as_dict)

        entries = self.__filter_request_by_symbols(request, entries)

        if len(entries) == 0:
            return self.__return_empty_result(pretty, as_df, as_dict)

        return self.dataframe_to_transaction_output(entries, request, pretty, as_dict=as_dict, as_df=as_df)

    def __filter_request_by_symbols(self, request, entries):
        symbols = request[settings.request_symbols]
        if symbols == ['*']:
            filter_by_symbol = entries
        else:
            filter_by_symbol = entries[entries[settings.database_column_symbol].isin(request[settings.request_symbols])]
        return filter_by_symbol

    def __filter_request_by_blockchain(self, request):
        all_entries = pd.DataFrame()
        if request[settings.request_blockchain] == ['*']:
            blockchains = self.__database.get_table_names()
        else:
            blockchains = request[settings.request_blockchain]

        for blockchain in blockchains:
            new_entries = self.__database.get_row_range(blockchain, 'timestamp',
                                                        request[settings.request_from_time] + 1, int(time.time()))
            if new_entries is None:
                log.warning("Data request for blockchain {} which isn't in database".format(blockchain))
                continue
            all_entries = all_entries.append(new_entries)
        return all_entries

    def dataframe_to_transaction_output(self, df, request=None, pretty=False, as_dict=False, as_df=False):

        sorted_by_time = df.sort_values('timestamp', ascending=True)

        if request is not None and request[settings.request_maximum_results] >= 0:
            sorted_by_time = sorted_by_time.tail(request[settings.request_maximum_results])

        if as_df:
            sorted_by_time.reset_index(drop=True, inplace=True)
            return sorted_by_time
        return self.__make_result_string(sorted_by_time, pretty, as_dict)

    def __return_empty_result(self, pretty, as_df, as_dict):
        if as_df:
            return pd.DataFrame()
        elif as_dict:
            return []
        else:
            return ''

    def __make_result_string(self, results, pretty, as_dict):

        output = ''
        output_list = []
        for index, result in results.iterrows():
            try:
                if result[settings.database_column_to_owner] == '':
                    result[settings.database_column_to_owner] = 'unknown'
                if result[settings.database_column_from_owner] == '':
                    result[settings.database_column_from_owner] = 'unknown'
                if as_dict:
                    output_dict = dict()
                    output_dict['timestamp'] = self.__make_time_string(result, pretty)[:-1]
                    output_dict['text'] = self.__make_amount_string(result, pretty) + self.__make_transfer_string(
                        result, pretty)[:-1]
                    output_list.append(output_dict)
                else:
                    output = output + self.__make_time_string(result, pretty) + self.__make_amount_string(
                        result, pretty) + self.__make_transfer_string(result, pretty)
            except Exception as e:
                log.error("Invalid column names found in database. Exception {}".format(e))

        log.debug("Successful data request returned {} results".format(len(results)))
        if as_dict:
            return output_list
        else:
            return output[:-1]

    def __make_time_string(self, result, pretty):
        if pretty:
            return Fore.YELLOW + Reader.to_local_time(
                result[settings.database_column_timestamp]) + " " + Style.RESET_ALL
        else:
            return Reader.to_local_time(result[settings.database_column_timestamp]) + " "

    def __make_amount_string(self, result, pretty):
        if pretty:
            output = Fore.WHITE + str("{:.2f}".format(
                result[settings.database_column_amount])) + " " + Fore.RED + result[settings.database_column_symbol]
            if result[settings.database_column_amount_usd] < 1000000:
                output = output + Fore.CYAN + " (" + Reader.format_currency(
                    result[settings.database_column_amount_usd]) + " USD) "
            elif result[settings.database_column_amount_usd] < 20000000:
                output = output + Fore.CYAN + Style.BRIGHT + " (" + Reader.format_currency(
                    result[settings.database_column_amount_usd]) + " USD) "
            else:
                output = output + ' ' + Fore.CYAN + Style.BRIGHT + UNDERLINE + "(" + Reader.format_currency(
                    result[settings.database_column_amount_usd]) + " USD)"
            return output + Style.RESET_ALL + ' '
        else:
            return str("{:.2f}".format(result[settings.database_column_amount])) + " " + result[
                settings.database_column_symbol] + " (" + Reader.format_currency(
                    result[settings.database_column_amount_usd]) + " USD) "

    def __make_transfer_string(self, result, pretty):
        if pretty:
            if result[settings.database_column_transaction_type] == 'transfer':
                output = 'transferred from ' + Fore.BLUE + result[settings.database_column_from_owner]  \
                        + Style.RESET_ALL + ' to ' + Fore.BLUE + result[settings.database_column_to_owner] \
                         + Style.RESET_ALL + '.\n'
            elif result[settings.database_column_transaction_type] == 'burn':
                output = Fore.RED + 'burned' + Style.RESET_ALL + ' at ' +  \
                        Fore.BLUE + result[settings.database_column_from_owner] + Style.RESET_ALL + '.\n'
            else:
                output = result[settings.database_column_transaction_type] + ' from ' +  \
                        Fore.BLUE + result[settings.database_column_from_owner]  \
                        + Style.RESET_ALL + ' to ' + Fore.BLUE + result[settings.database_column_to_owner] \
                        + Style.RESET_ALL + '.\n'

            return output
        else:
            return "transferred from " + result[settings.database_column_from_owner] + \
                    ' to ' + result[settings.database_column_to_owner] + '.' + '\n'

    def __check_data_request_keys(self, request):
        try:
            dummy = request[settings.request_blockchain]
            dummy = request[settings.request_from_time]
            dummy = request[settings.request_symbols]
            dummy = request[settings.request_maximum_results]
            dummy = request[settings.request_output_format]
            _ = dummy
        except KeyError:
            log.error("Invalid keys supplied in data request {}".format(request))
            return False
        return True

    def format_currency(value):
        return str(f'{value:,.2f}'.replace('$-', '-$'))

    def to_local_time(unix_timestamp):
        return datetime.datetime.fromtimestamp(unix_timestamp).astimezone(tz.tzlocal()).strftime(
            settings.request_time_format)

    def from_local_time(iso8601):
        return int((parser.parse(iso8601).astimezone(tz.tzlocal()).strftime('%s')))
