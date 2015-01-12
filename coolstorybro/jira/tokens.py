from sqlalchemy.orm.exc import NoResultFound

class TokenManager(object):
    def __init__(self, adapter):
        self._adapter = adapter

    def set(self, client_key, secret):
        return self._adapter.set(client_key, secret)

    def get(self, client_key):
        return self._adapter.get(client_key)

    def delete(self, client_key):
        return self._adapter.delete(client_key)


class SQLAlchemyAdapter(object):
    def __init__(self, session, cls):
        self._session = session
        self._cls = cls

    def get(self, client_key):
        return str(self._get_object(client_key).client_secret)

    def _get_object(self, client_key):
            return self._session.query(self._cls).filter(self._cls.client_key==client_key).one()

    def set(self, client_key, secret):
        try:
            c = self._get_object(client_key)
            c.client_secret = secret
        except NoResultFound:
            c = self._cls(client_key=client_key, client_secret=secret)
        self._session.add(c)

    def delete(self, client_key):
        try:
            c = self.get(client_key)
            self._session.delete(c)
        except NoResultFound:
            pass