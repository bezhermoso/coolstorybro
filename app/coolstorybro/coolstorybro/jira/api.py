import requests
import json
from urllib import (
    quote,
    urlencode
)
# from urlparse import (
#     urlparse,
#     unquote,
#     parse_qsl
# )
from datetime import (
    datetime
)
from hashlib import (
    sha256
)
import jwt
import re

class Client(object):
    def __init__(self, host, issuer, secret):
        self._host = host
        self._issuer = issuer
        self._secret = secret
        self._jwt_headers = {
            'typ': 'JWT',
            'alg': 'HS256'
        }

    def _strip_host(self, uri):
        stripped = re.sub('^%s' % self._host, '', uri)
        return stripped

    def get(self, uri, data=None, **kwargs):
        uri = self._strip_host(uri)
        data = {} if data is None else data
        jwt = self._create_jwt('GET', uri, data, **kwargs)
        req = requests.get(self._host + uri, data=data, headers={
            'Authorization': 'JWT %s' % jwt
        })
        return req

    def post(self, uri, data, query_params=None, **kwargs):
        return self.make_request('POST', uri, data, query_params, **kwargs)

    def put(self, uri, data, query_params=None, **kwargs):
        return self.make_request('PUT', uri, data, query_params, **kwargs)

    def delete(self, uri, data, query_params=None, **kwargs):
        return self.make_request('DELETE', uri, data, query_params, **kwargs)

    def make_request(self, method, uri, data, query_params=None, **kwargs):

        if method.upper() == 'GET':
            raise ValueError('Only use POST, PUT, or DELETE.')

        uri = self._strip_host(uri)
        query_params = query_params if query_params is not None else {}
        query_string = urlencode(query_params)
        if len(query_string) > 0:
            actual_uri = '%s?%s' % (uri, query_string)
        else:
            actual_uri = uri

        if not actual_uri.startswith('/'):
            actual_uri = '/%s' % actual_uri

        jwt = self._create_jwt(method.upper(), uri, query_params, **kwargs)
        req = getattr(requests, method.lower())(self._host + actual_uri, data=json.dumps(data), headers={
            'Authorization': 'JWT %s' % jwt,
            'Content-Type': 'application/json'
        })
        return req

    def _qhash(self, method, uri, get_params=None):
        """ Implement hashing from:
            https://developer.atlassian.com/static/connect/docs/concepts/understanding-jwt.html
        """
        hash_parts = [method.upper()]

        uri = uri if len(uri) > 0 else '/'
        uri = uri if uri.startswith('/') else ('/%s' % uri)
        uri = uri.replace('&', quote('&'))
        hash_parts.append(uri)

        query_string = ''
        if get_params is not None and len(get_params) > 0:
            sorted_params = self._sort_get_params(get_params.items())
            # Flatten repeating values:
            flattened = {}
            for (key, value) in sorted_params:
                if key == 'jwt':
                    continue
                if key in flattened:
                    flattened[key] += ',' + value
                else:
                    flattened[key] = value
            query_string = urlencode(flattened)
        hash_parts.append(query_string)

        query_hash = '&'.join(hash_parts).encode('utf-8')

        return sha256(query_hash).hexdigest()

    def _sort_get_params(self, tuples):
        sorted = list(tuples)
        sorted.sort(key=lambda t: (quote(t[0]), quote(t[1])))
        return sorted

    @staticmethod
    def _sort_params_key(t):
        return quote(t[0]), quote(t[1])

    def _create_jwt(self, method, uri, query_params, **kwargs):
        """ Generate JWT token according to guidelines:
            https://developer.atlassian.com/static/connect/docs/concepts/understanding-jwt.html
        """
        now = datetime.utcnow()
        iat = long(float(now.strftime('%s')))
        claim = {
            'iss': self._issuer,
            'iat': iat,
            'exp': iat + 60,  # Expires in a minute.
            'qsh': self._qhash(method, uri, query_params)
        }
        if kwargs.has_key('impersonate'):
            claim['sub'] = kwargs['impersonate']

        return jwt.encode(
            payload=claim,
            headers=self._jwt_headers,
            key=self._secret,
            algorithm=self._jwt_headers['alg'])