from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    String,
    Boolean
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

import json

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class JiraInstance(Base):
    __tablename__ = 'jira_instances'
    id = Column(Integer, primary_key=True)
    client_key = Column(String(100), unique=True, nullable=False)
    client_secret = Column(String(255))

class ProjectConfig(Base):
    __tablename__ = 'project_config'
    client_key = Column(String(100), nullable=False, primary_key=True)
    project_id = Column(String(50), nullable=False, primary_key=True)
    configuration = Column(Text, nullable=True, default='{}')
    enabled = Column(Boolean, default=False)

    def json_config(self):
        return json.loads(self.configuration)

    def set_json_config(self, config):
        self.configuration = json.dumps(config)

    def is_goal(self, issue_type, status):
        config = self.json_config()
        issue_type = str(issue_type)
        status = str(status)
        return config.has_key(issue_type) and config.get(issue_type).has_key(status)