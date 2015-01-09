from pyramid.config import Configurator
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from random import random
from .jira.tokens import (
    TokenManager,
    SQLAlchemyAdapter
)
from .models import (
    DBSession,
    Base,
    JiraInstance,
)

def db(request):
    maker = request.registry.db_session_maker
    session = maker()

    def cleanup(request):
        if request.exception is not None:
            session.rollback()
        else:
            session.commit()
        session.close()
    request.add_finished_callback(cleanup)
    return session


def jira_token_mgr(request):
    db_session = request.db_session
    adapter = SQLAlchemyAdapter(db_session, JiraInstance)
    return TokenManager(adapter)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    config = Configurator(settings=settings)

    config.registry.db_session_maker = sessionmaker(bind=engine)

    config.include('pyramid_chameleon')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')

    config.add_request_method(jira_token_mgr, 'jira_token_mgr', reify=True)
    config.add_request_method(db, 'db_session', reify=True)

    config.add_route('webhook', '/webhook/{event}')
    config.scan()
    return config.make_wsgi_app()
