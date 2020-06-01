[![Build Status](https://travis-ci.org/stuianna/whaleAlert.svg?branch=master)](https://travis-ci.org/stuianna/whaleAlert)
![Codecov](https://img.shields.io/codecov/c/github/stuianna/whaleAlert)
![GitHub](https://img.shields.io/github/license/stuianna/whaleAlert)

# WhaleAlert - Cryptocurrecy Whale Alert API Logger

A python API and script for requesting, parsing and storing the latest cryptocurrency data availalbe using the [Whale Alert Free API](https://whale-alert.io/). Data entries are stored in a SQLite3 database, with CLI features for querying data and logger status.

## Using the API

To use any feature of this API, an account and free API key needs to be obtained from [Whale Alert](https://whale-alert.io/)

```python3
>>> import time
>>> from pprint import pprint  # For formatted dictionary printing
>>> from whalealert.whalealert import WhaleAlert
>>> whale = WhaleAlert()

# Specify a single transaction from the last 10 minutes
>>> start_time = int(time.time() - 600)
>>> api_key = 'your-key-to-stonks'
>>> transaction_count_limit = 1

>>> success, transactions, status = whale.get_transactions(start_time, api_key=api_key, limit=transaction_count_limit)
>>> success
true

>>> pprint(transactions)
[{'amount': 1000000,
  'amount_usd': 997749.6,
  'blockchain': 'ethereum',
  'from': {'address': '46705dfff24256421a05d056c29e81bdc09723b8',
           'owner': 'huobi',
           'owner_type': 'exchange'},
  'hash': 'd1e52138ecf959e580fc3167b10977dfe3114f883136bebd3317f5b5c35762b4',
  'id': '710406265',
  'symbol': 'USDT',
  'timestamp': 1591028741,
  'to': {'address': 'c1b5915fd74cce2a4a9b889b0bc1efcac6af45af',
         'owner': '',
         'owner_type': 'unknown'},
  'transaction_count': 1,
  'transaction_type': 'transfer'}]

>>> pprint(status)
{'error_code': 200,
 'error_message': '',
 'timestamp': '2020-06-01T19:35:19.051584',
 'transaction_count': 1}
```

## Using the Data Logging Function

The module automatically installs a python script `whaleAlertLogger` and adds it to your python binary directory.

The python script automatically polls the Whale Alert API for new transactions and saves them in an SQLite3 database.

```bash
# Install the module and script
pip install whaleAlert

# Initialise the required configuration, supplying your API key.
whaleAlertLogger -a 'your-api-key' -g

# Start the logger.
whaleAlertLogger &

# Query the latest whale tranactions
whaleAlertLogger -q 
06/01/2020 20:01:25 697730.00 USDT (698,289.70 USD) transferred from unknown to unknown.
06/01/2020 20:02:59 1000000.00 USDT (996,660.90 USD) transferred from unknown to huobi.

# Query the latest 3 transactions, from the ethereum blockchain, with the tag USDT.
whaleAlertLogger -q -b ethereum -t USDT
06/01/2020 19:56:51 1000000.00 USDT (997,847.70 USD) transferred from unknown to unknown.
06/01/2020 20:01:25 697730.00 USDT (698,289.70 USD) transferred from unknown to unknown.
06/01/2020 20:02:59 1000000.00 USDT (996,660.90 USD) transferred from unknown to huobi.

# Get the  status of the logger.
whaleAlertLogger -s
Last successful call 0 minutes ago, health 100.0%

# Kill any running logger instance
whaleAlertLogger -k

# Convert the SQLite3 database to an Excel file
whaleAlertLogger -x
```

## Stored Database and Configuration

When the logger is initialised, it creates a directory structure inside `$XDG_CONFIG_HOME`. This could be `~/.local/share/whaleAlertLogger` or `~/.config/whaleAlertLogger`, use `echo $XDG_CONFIG_HOME` to find the location on your system.

The directory structure is as follows:

```bash
whaleAlertLogger
├── config.ini
└── data
    ├── whaleAlert.db
    ├── log
    └── status.ini
```

**config.ini**

Contains configuration parameters used. Change any of these settings and restart the logger to apply them. Values shown are the default.
```ini
[API]
api_private_key = your-private-key-here
request_interval_seconds = 30
minimum_transaction_value 500000
historical_limit 3599
```

**whaleAlert.db**

A SQLite3 database containing all data retreived by the logger. The database contains a separate table, named after each unique blockchain. [SQLitebrower](https://sqlitebrowser.org/), is a good tool for browsing databases, or use `whaleAlertLogger -x` to convert the database to an Excel file for viewing.

**status.ini**

Contains information on the status of the logger.
```ini
[Last Successful Call]
timestamp = 2020-06-01T20:21:37.859798
transaction_count = 1

[Last Failed Call]
timestamp = 2020-06-01T13:46:27.936514
error_code = 5
error_message = Internal error: Error parsing JSON object from received response.

[Current Session]
successful_calls = 5441
failed_calls = 10
success_rate = 99.82
health = 100.0

[All Time]
successful_calls = 38651
failed_calls = 364
success_rate = 99.07
```

**log**

Runtime logs stored by the Python logging module.

