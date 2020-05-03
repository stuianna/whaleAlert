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

#Status file definitions
status_file_last_good_call_section_name = 'Last Successful Call'
status_file_last_failed_secion_name = 'Last Failed Call'

status_file_option_timeStamp = 'timestamp'
status_file_option_error_code = 'error_code'
status_file_option_error_message = 'error_message'

status_file_all_time_section_name = 'All Time'
status_file_current_session_section_name = 'Current Session'

status_file_option_successful_calls = 'successful_calls'
status_file_option_failed_calls = 'failed_calls'
status_file_option_success_rate = 'success_rate'
status_file_option_health = "health"
