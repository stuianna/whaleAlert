# Filenames
input_configuation_filename = "config.ini"
data_file_directory = "data"
log_file_directory = data_file_directory
status_file_directory = data_file_directory
log_file_name = "log"
database_file_name = 'whaleAlert.db'
status_file_name = 'status.ini'
appNameDirectory = 'whaleAlertLogger'

# Input configuration file
API_section_name = "API"
API_option_private_key = "api_private_key"
API_option_privatate_key_default = 'your-private-key-here'
API_option_interval = 'request_interval_seconds'
API_option_interval_default = 60
API_option_minimum_value = 'minimum_transaction_value'
API_option_minimum_value_default = 500000
API_option_historical_limit = 'historical_limit'
API_option_historical_limit_default = 3599

# Status file definitions
status_file_last_good_call_section_name = 'Last Successful Call'
status_file_last_failed_secion_name = 'Last Failed Call'

status_file_option_transaction_count = 'transaction_count'
status_file_option_timeStamp = 'timestamp'
status_file_option_error_code = 'error_code'
status_file_option_error_message = 'error_message'

status_file_all_time_section_name = 'All Time'
status_file_current_session_section_name = 'Current Session'

status_file_option_successful_calls = 'successful_calls'
status_file_option_failed_calls = 'failed_calls'
status_file_option_success_rate = 'success_rate'
status_file_option_health = "health"

# Database definitions
database_column_blockchain = 'blockchain'
database_column_symbol = 'symbol'
database_column_id = 'id'
database_column_transaction_type = 'transaction_type'
database_column_hash = 'hash'
database_column_from_address = 'from_address'
database_column_from_owner = 'from_owner'
database_column_from_owner_type = 'from_owner_type'
database_column_to_address = 'to_address'
database_column_to_owner = 'to_owner'
database_column_to_owner_type = 'to_owner_type'
database_column_timestamp = 'timestamp'
database_column_amount = 'amount'
database_column_amount_usd = 'amount_usd'
database_column_transaction_count = 'transaction_count'

database_table_identifier = 'blockchain'

database_columns = {
    database_column_blockchain: 'TEXT',
    database_column_symbol: 'TEXT',
    database_column_id: 'TEXT',
    database_column_transaction_type: 'TEXT',
    database_column_hash: 'TEXT',
    database_column_from_address: 'TEXT',
    database_column_from_owner: 'TEXT',
    database_column_from_owner_type: 'TEXT',
    database_column_to_address: 'TEXT',
    database_column_to_owner: 'TEXT',
    database_column_to_owner_type: 'TEXT',
    database_column_timestamp: 'NUMERIC',
    database_column_amount: 'REAL',
    database_column_amount_usd: 'REAL',
    database_column_transaction_count: 'NUMERIC'
}

# Whale Alert API
whale_get_transactions_url = 'https://api.whale-alert.io/v1/transactions'
whale_retries_on_failure = 3
whale_call_timeout_seconds = 10

whale_error_message = 'message'

whale_success_result = 'result'
whale_success_cursor = 'cursor'
whale_success_count = 'count'
whale_success_transactions = 'transactions'

whale_transaction_blockchain = 'blockchain'
whale_transaction_symbol = 'symbol'
whale_transaction_id = 'id'
whale_transaction_transaction_type = 'transaction_type'
whale_transaction_hash = 'hash'
whale_transaction_from = 'from'
whale_transaction_address = 'address'
whale_transaction_owner = 'owner'
whale_transaction_owner_type = 'owner_type'
whale_transaction_to = 'to'
whale_transaction_timestamp = 'timestamp'
whale_transaction_amount = 'amount'
whale_transaction_amount_usd = 'amount_usd'
whale_transaction_transaction_count = 'transaction_count'

# Puslisher settings
health_list_length = 30

# Data request settings
request_blockchain = 'blockchain'
request_symbols = 'symbols'
request_from_time = 'from_time'
request_output_format = 'output_format'
request_maximum_results = 'maximum_results'

request_format = {
    request_blockchain: [],
    request_symbols: [],
    request_from_time: 0,
    request_output_format: 'str',
    request_maximum_results: 1
}

request_time_format = "%m/%d/%Y %H:%M:%S"

maximum_stored_latest_transaction = 1000
