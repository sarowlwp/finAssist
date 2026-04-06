from storage.portfolio import PortfolioStore, PortfolioItem
from storage.settings import SettingsStore, UserSettings
from pathlib import Path
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


def test_portfolio_store_crud():
    """Test portfolio store CRUD operations"""
    # 创建内存中的 SQLite 数据库和会话
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # 创建所有表
    from models import Base
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create store
            store = PortfolioStore(db, temp_path)

            # Test initial state - note: store creates initial data!
            initial_items = store.get_all()
            assert len(initial_items) >= 0

            # Clear initial data if needed
            for item in store.get_all():
                store.remove_item(item.ticker)
            assert len(store.get_all()) == 0

            # Test add item
            item = PortfolioItem(
                ticker="AAPL",
                quantity=100,
                cost_price=150.0,
                note="Test note"
            )
            store.add_item(item)
            assert len(store.get_all()) == 1

            # Test get item
            portfolio = store.get_all()
            assert portfolio[0].ticker == "AAPL"
            assert portfolio[0].quantity == 100

            retrieved = store.get_by_ticker("AAPL")
            assert retrieved is not None
            assert retrieved.ticker == "AAPL"

            # Test update item
            store.update_item("AAPL", quantity=150)
            updated = store.get_by_ticker("AAPL")
            assert updated is not None
            assert updated.quantity == 150

            # Test delete item
            store.remove_item("AAPL")
            assert len(store.get_all()) == 0

    finally:
        db.close()


def test_settings_store():
    """Test settings store"""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        store = SettingsStore(temp_path)

        # Test initial state
        settings = store.load()
        assert settings.investment_style == "balanced"

        # Test update investment style
        store.update_investment_style("conservative")
        settings = store.load()
        assert settings.investment_style == "conservative"

        # Test update LLM config
        new_config = {
            "provider": "openai",
            "model": "gpt-4",
            "temperature": 0.5
        }
        store.update_llm_config(new_config)
        settings = store.load()
        assert settings.llm_config["provider"] == "openai"
        assert settings.llm_config["model"] == "gpt-4"
