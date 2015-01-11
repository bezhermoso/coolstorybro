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
    configuration = Column(Text, nullable=True)
    enabled = Column(Boolean, default=False)