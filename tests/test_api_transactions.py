import unittest
from unittest import mock
import logging
from requests.models import Response
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import whalealert.settings as settings
import json
import datetime


class WhaleAlertAPI(unittest.TestCase):

    def setUp(self):
        pass

    def test_test(self):
        self.assertIs(True,True)
