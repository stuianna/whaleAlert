import logging
import time
import datetime
import pandas as pd
import whalealert.settings as settings
from dateutil import tz

log = logging.getLogger(__name__)


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

    def data_request(self, request):

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
            new_entries = self.__database.get_row_range(blockchain, 'timestamp', request[settings.request_from_time],
                                                        int(time.time()))
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

        sorted_by_time = filter_by_symbol.sort_values('timestamp', ascending=True)

        if request[settings.request_maximum_results] >= 0:
            sorted_by_time = sorted_by_time.tail(request[settings.request_maximum_results])

        results = self.__make_result_string(sorted_by_time)
        return results

    def __make_result_string(self, results):

        output = ''
        for index, result in results.iterrows():
            try:
                if result[settings.database_column_to_owner] == '':
                    result[settings.database_column_to_owner] = 'unknown'
                if result[settings.database_column_from_owner] == '':
                    result[settings.database_column_from_owner] = 'unknown'
                output = output + Reader.to_local_time(result[settings.database_column_timestamp]) + " " + str(
                    "{:.2f}".format(result[settings.database_column_amount])) + " " + result[
                        settings.database_column_symbol] + " (" + Reader.format_currency(
                            result[settings.database_column_amount_usd]) + " USD) " + "transferred from " + result[
                                settings.database_column_from_owner] + ' to ' + result[
                                    settings.database_column_to_owner] + '.' + '\n'
            except Exception as e:
                log.error("Invalid column names found in database. Exception {}".format(e))

        log.debug("Successful data request returned {} results".format(len(results)))
        return output

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
