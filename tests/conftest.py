import pytest
import logging
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import Base
from datetime import datetime, timedelta

# Настройка логирования для тестов
@pytest.fixture(autouse=True)
def setup_logging():
    log_dir = Path("tests/logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "test.log"),
            logging.StreamHandler()
        ]
    )

# Фикстура для тестовой базы данных
@pytest.fixture(scope="session")
def test_db_engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="function")
def test_db(test_db_engine):
    TestingSessionLocal = sessionmaker(bind=test_db_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_db_engine)
        Base.metadata.create_all(bind=test_db_engine)

# Фикстура для тестового клиента FastAPI
@pytest.fixture
def client(test_db):
    return TestClient(app) 