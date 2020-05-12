"""
API wrapper for getting transactions from Whale Alert API
"""

import logging
import json
import time
import datetime
from requests import Session
from requests.exceptions import Timeout, TooManyRedirects
import whalealert.settings as settings

log = logging.getLogger(__name__)


class Transactions():
    """
    API wrapper for getting transactions from Whale Alert API
    """
    def __init__(self):
        self.__session = Session()
        self.__last_timestamp = int(time.time())
        self.__last_cursor = None
        self.__call_return_time = int(time.time())
        logging.debug("Transactions object created")

    def get_last_timestamp(self):
        """ Get the timestamp of the last successful call

        Returns:
        Unix timestamp (int): Last successful call time.
        """
        return self.__last_timestamp

    def get_last_cursor(self):
        """ Get the API cursor for the last successful call.

        Returns:
        cursor (string): Last successful API call cursor provided by Whale Alert
        """
        return self.__last_cursor

    def get_transactions(self, start_time, end_time, api_key, cursor, min_value, limit):
        """ Make an API call to Whale Alert to get the latest transactions.

        The free API has the following limitions:
        - Historical limit of 3600 seconds. (start_time)
        - Minimum transactino value is 500000 USD
        - Limit of 100 transactions

        Parameters:
        start_time (int): Unix timestamp from which to start listing transactions. (exclusive)
        end_time (int): Unix timestamp from where to stop listing transactions (inclusive). Use None to get to current time.
        api_key (str): The API key to use for the transaction.
        cursor (str): The pagnation cursor from a previous transaction. Use None to ignore this parameter.
        min_value (int): The minimum value of transaction to return.
        limit (int): The maximum number of transactions to return (maximum = 100)

        Returns:
        success (bool) : If true, then a successful call was made (Return code of 200). Return false otherwise.
        transactions (list or None):
        - success = True: A list containing a dictionary for each transaction.
        - success = False: None
        status (dict): A dictionary containing the timestamp, error_code and error_message for the transaction.
        """
        parameters = self.__form_request(start_time, end_time, api_key, cursor, min_value, limit)
        log.debug("Attempting API call at '{}' with parameters '{}'".format(settings.whale_get_transactions_url,
                                                                            parameters))

        success, response, status = self.__attempt_call(parameters)
        if success is not True:
            return success, None, status

        success, transactions, status = self.__check_response(response)
        return success, transactions, status

    def __attempt_call(self, parameters):
        retries = settings.whale_retries_on_failure
        attempt = 1
        while retries >= 0:
            try:
                response = self.__session.get(settings.whale_get_transactions_url,
                                              params=parameters,
                                              timeout=settings.whale_call_timeout_seconds)
                self.__call_return_time = int(time.time())
                retries = -1
            except ConnectionError:
                retries, attempt, done = self.__evalulate_attempt(retries, attempt)
                if not done:
                    continue
                status = self.__make_custom_status(1, "Internal error: Connection exception when conduction API call",
                                                   0)
                return False, None, status
            except Timeout:
                retries, attempt, done = self.__evalulate_attempt(retries, attempt)
                if not done:
                    continue
                status = self.__make_custom_status(2, "Internal error: Timeout exception when conduction API call", 0)
                return False, None, status
            except TooManyRedirects:
                retries, attempt, done = self.__evalulate_attempt(retries, attempt)
                if not done:
                    continue
                status = self.__make_custom_status(
                    3, "Internal error: TooManyRedirect exception when conduction API call", 0)
                return False, None, status
            except Exception as e_r:
                retries, attempt, done = self.__evalulate_attempt(retries, attempt)
                if not done:
                    continue
                status = self.__make_custom_status(4,
                                                   "Internal error: Exception {} when conduction API call".format(e_r),
                                                   0)
                return False, None, status
        return True, response, None

    def __evalulate_attempt(self, retries, attempt):
        if retries >= 1:
            retries = retries - 1
            time.sleep(2 * attempt)
            log.warning("Exception occurred on API call attempt {} of {}".format(attempt,
                                                                                 settings.whale_retries_on_failure))
            attempt = attempt + 1
            done = False
        else:
            done = True
        return retries, attempt, done

    def __check_response(self, response):
        try:
            json_fields = json.loads(response.text)
        except json.decoder.JSONDecodeError:
            status = self.__make_custom_status(5, "Internal error: Error parsing JSON object from received response", 0)
            return False, None, status
        except Exception as e:
            status = self.__make_custom_status(
                6,
                "Internal error: Exception {} when parsing JSON object from received response. Response =  {}".format(
                    e, response.text), 0)
            return False, None, status

        if response.status_code != 200:
            status = self.__parse_error_response(json_fields, response.status_code)
            return False, None, status

        success, transactions, status = self.__parse_good_response(json_fields)
        return success, transactions, status

    def __parse_good_response(self, json_fields):
        good_keys, count, status = self.__check_main_keys(json_fields)
        if good_keys is False:
            return False, None, status

        if count == 0:
            log.info("Successful API call returned {} transactions".format(count))
            return True, [], self.__make_custom_status(200, '', 0)

        good_keys, transactions, status = self.__check_transactions_keys(json_fields)
        if good_keys is False:
            return False, None, status

        self.__last_cursor = json_fields[settings.whale_success_cursor]
        self.__last_timestamp = self.__call_return_time
        log.info("Successful API call returned {} transactions".format(len(transactions)))
        return True, transactions, self.__make_custom_status(200, '', count)

    def __check_transactions_keys(self, json_fields):
        for transaction in json_fields[settings.whale_success_transactions]:
            try:
                dummy = transaction[settings.whale_transaction_blockchain]
                dummy = transaction[settings.whale_transaction_symbol]
                dummy = transaction[settings.whale_transaction_id]
                dummy = transaction[settings.whale_transaction_transaction_type]
                dummy = transaction[settings.whale_transaction_hash]
                dummy = transaction[settings.whale_transaction_from][settings.whale_transaction_address]
                dummy = transaction[settings.whale_transaction_to][settings.whale_transaction_address]
                dummy = transaction[settings.whale_transaction_timestamp]
                dummy = transaction[settings.whale_transaction_amount]
                dummy = transaction[settings.whale_transaction_amount_usd]
                dummy = transaction[settings.whale_transaction_transaction_count]

                owner_type = transaction[settings.whale_transaction_from][settings.whale_transaction_owner_type]
                transaction[settings.whale_transaction_symbol] = transaction[settings.whale_transaction_symbol].upper()
                if owner_type != 'unknown':
                    dummy = transaction[settings.whale_transaction_from][settings.whale_transaction_owner]
                else:
                    transaction[settings.whale_transaction_from][settings.whale_transaction_owner] = ''

                owner_type = transaction[settings.whale_transaction_to][settings.whale_transaction_owner_type]
                if owner_type != 'unknown':
                    dummy = transaction[settings.whale_transaction_to][settings.whale_transaction_owner]
                else:
                    transaction[settings.whale_transaction_to][settings.whale_transaction_owner] = ''
            except KeyError:
                return False, None, self.__make_custom_status(
                    10, 'Internal error: Error with transactions JSON keys, bad transaction = {}'.format(transaction),
                    0)
        return True, json_fields[settings.whale_success_transactions], None

    def __check_main_keys(self, json_fields):
        try:
            dummy = json_fields[settings.whale_success_result]
            dummy = json_fields[settings.whale_success_cursor]
            count = json_fields[settings.whale_success_count]
            if count > 0:
                transactions = json_fields[settings.whale_success_transactions]
                if len(transactions) != count:
                    status = self.__make_custom_status(
                        8, "Internal error: Transaction count doesn't match reported count. Response = {}".format(
                            json_fields), 0)
                    return False, 0, status
        except KeyError:
            status = self.__make_custom_status(
                9, "Internal error: Problem parsing main keys. Response = {}".format(json_fields), 0)
            return False, 0, status
        return True, count, None

    def __parse_error_response(self, json_response, code):
        try:
            message = json_response[settings.whale_error_message]
        except Exception as e_r:
            code = 7
            message = "Internal error: Cannot read message from error response. Response = {}, Exception = {}".format(
                json_response, e_r)
        return self.__make_custom_status(code, message, 0)

    def __make_custom_status(self, errNo, message, transaction_count):
        custom_status = dict()
        custom_status[settings.status_file_option_timeStamp] = str(datetime.datetime.now().isoformat())
        custom_status[settings.status_file_option_error_code] = errNo
        custom_status[settings.status_file_option_error_message] = message
        custom_status[settings.status_file_option_transaction_count] = transaction_count
        if errNo != 200:
            log.error(message)
        return custom_status

    def __form_request(self, start_time, end_time, api_key, cursor, min_value, limit):
        call_parameters = {}

        # Required for every call
        call_parameters['api_key'] = api_key
        call_parameters['start'] = start_time
        call_parameters['min_value'] = min_value
        call_parameters['limit'] = limit

        if end_time is not None:
            call_parameters['end'] = end_time

        if cursor is not None:
            call_parameters['cursor'] = cursor

        return call_parameters
