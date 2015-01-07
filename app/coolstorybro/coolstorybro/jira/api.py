import requests
import json
import re

class Client(object):
    def __init__(self, host, secret):
        self._host = host
        self._secret = secret

    def post(self, post_data):
        pass

    def get(self, data):
        pass

    def _request(self, method, data):
        pass

    pass