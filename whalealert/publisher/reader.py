import logging
import time
import datetime
import pandas as pd
from colorama import Fore
from colorama import Style
import whalealert.settings as settings
from dateutil import tz

log = logging.getLogger(__name__)
UNDERLINE = '\033[4m'


class Reader():
    """ Reading Whale Alert API status and database results"""
    def __init__(self, status=None, database=None):
        self.__status = status
        self.__database = database
        if status is not None:
            log.debug("Pulisher started with initial status {}".format(status.get_expectations()))

    def get_status_object(self):
        """ Return the status object used"""
        return self.__status

    def get_database(self):
        """Return the database object used"""
        return self.__database

    def data_request(self, request, pretty=False, as_df=False, as_dict=False):

        if self.get_database() is None:
            log.error("Requesting data from a database with no working directory")
            return ''

        if self.__check_data_request_keys(request) is False:
            return ''

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

        if len(all_entries) == 0:
            return ''

        symbols = request[settings.request_symbols]
        if symbols == ['*']:
            filter_by_symbol = all_entries
        else:
            filter_by_symbol = all_entries[all_entries[settings.database_column_symbol].isin(
                request[settings.request_symbols])]

        return self.dataframe_to_transaction_output(filter_by_symbol, request, pretty, as_dict=as_dict, as_df=as_df)

    def dataframe_to_transaction_output(self, df, request=None, pretty=False, as_dict=False, as_df=False):

        sorted_by_time = df.sort_values('timestamp', ascending=True)

        if request is not None and request[settings.request_maximum_results] >= 0:
            sorted_by_time = sorted_by_time.tail(request[settings.request_maximum_results])

        if as_df:
            return sorted_by_time
        return self.__make_result_string(sorted_by_time, pretty, as_dict)

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
                    output_dict['timestamp'] = self.__make_time_string(result, pretty)
                    output_dict['text'] = self.__make_amount_string(result, pretty) + self.__make_transfer_string(
                        result, pretty)
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
