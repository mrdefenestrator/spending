import pytest
from sqlalchemy import create_engine
from spending.models import metadata


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return engine


@pytest.fixture
def conn(engine):
    with engine.connect() as connection:
        yield connection
