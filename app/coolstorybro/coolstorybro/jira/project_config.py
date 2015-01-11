import json
from sqlalchemy.orm.exc import (
    NoResultFound
)

class ConfigManager(object):

    def __init__(self, db_session, cls):
        self._session = db_session
        self._cls = cls
        pass

    def save_data(self, client_key, project_id, configuration):
            try:
                pc = self.get_config(client_key, project_id)
                pc.configuration = json.dumps(configuration)
            except NoResultFound:
                pc = self._cls(client_key=client_key, project_id=project_id, configuration=json.dumps(configuration))
            self._session.add(pc)

    def get_config(self, client_key, project_id):
        return self._session.query(self._cls).filter(self._cls.client_key==client_key, self._cls.project_id==project_id).one()
        pass

    def has_config(self, client_key, project_id):
        try:
            self.get_config(client_key, project_id)
            return True
        except NoResultFound:
            return False

    def enable(self, client_key, project_id):
        try:
            pc = self.get_config(client_key, project_id)
            pc.enabled = True
        except NoResultFound:
            pc = self._cls(client_key=client_key, project_id=project_id, configuration='{}', enabled=True)
        self._session.add(pc)

    def disable(self, client_key, project_id):
        try:
            pc = self.get_config(client_key, project_id)
            pc.enabled = False
        except NoResultFound:
            pc = self._cls(client_key=client_key, project_id=project_id, configuration='{}', enabled=False)
        self._session.add(pc)

