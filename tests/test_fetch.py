from __future__ import unicode_literals, print_function
import ecbxrate
import pytest

def test_fetch_daily():
    """Test that we can fetch daily exchange rates."""
    store = ecbxrate.ExchangeRateStore('sqlite:///:memory:')
    store.create_tables()
    count, date = store.update()
    assert count != 0
    assert store.last_updated() is not None
    
def test_fetch_90():
    """Test that we can fetch 90 days of rates."""
    store = ecbxrate.ExchangeRateStore('sqlite:///:memory:')
    count, date = store.initialise(days=90)
    assert count != 0
    assert store.last_updated() is not None

def test_fetch_historic():
    """Test that we can fetch historic rates."""
    store = ecbxrate.ExchangeRateStore('sqlite:///:memory:')
    count, date = store.initialise()
    assert count != 0
    assert store.last_updated() is not None
