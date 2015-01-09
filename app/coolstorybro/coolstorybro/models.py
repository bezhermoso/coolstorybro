from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    String
    )

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

class JiraInstance(Base):
    __tablename__ = 'jira_instances'
    id = Column(Integer, primary_key=True)
    client_key = Column(String, unique=True)
    client_secret = Column(String)
