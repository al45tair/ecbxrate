from __future__ import unicode_literals, print_function
import ecbxrate
import pytest
import datetime

try:
    import cdecimal as decimal
except ImportError:
    import decimal

store = ecbxrate.ExchangeRateStore('sqlite:///:memory:')
store.initialise()

def test_latest_rate():
    """Test that we can fetch the latest rate."""
    d, e = store.get_rate('EUR', 'GBP', closest_rate=ecbxrate.BEFORE)

    assert e is not None

    d, e = store.get_rate('GBP', 'EUR', closest_rate=ecbxrate.BEFORE)

    assert e is not None

    d, e = store.get_rate('GBP', 'USD', closest_rate=ecbxrate.BEFORE)

    assert e is not None
    
def test_historic_rate():
    """Test that we can fetch a particular historic rate."""
    d, e = store.get_rate('EUR', 'GBP', as_of_date=datetime.date(2015,1,8))

    assert d == datetime.date(2015,1,8)
    assert e == decimal.Decimal('0.781100')

    # The closest rate option should have no effect
    d, e = store.get_rate('EUR', 'GBP', as_of_date=datetime.date(2015,1,8),
                          closest_rate=ecbxrate.BEFORE)

    assert d == datetime.date(2015,1,8)
    assert e == decimal.Decimal('0.781100')

    d, e = store.get_rate('EUR', 'GBP', as_of_date=datetime.date(2015,1,8),
                          closest_rate=ecbxrate.AFTER)

    assert d == datetime.date(2015,1,8)
    assert e == decimal.Decimal('0.781100')

def test_missing():
    """Test that we can tell if a rate was missing."""
    d, e = store.get_rate('EUR', 'GBP', as_of_date=datetime.date(2015,10,10))

    assert d == datetime.date(2015,10,10)
    assert e is None

def test_before():
    """Test that we can fetch the first rate before a missing rate."""
    d, e = store.get_rate('EUR', 'GBP', as_of_date=datetime.date(2015,10,10),
                          closest_rate=ecbxrate.BEFORE)

    assert d == datetime.date(2015,10,9)
    assert e == decimal.Decimal('0.740700')

def test_after():
    """Test that we can fetch the first rate after a missing rate."""
    d, e = store.get_rate('EUR', 'GBP', as_of_date=datetime.date(2015,10,10),
                          closest_rate=ecbxrate.AFTER)

    assert d == datetime.date(2015,10,12)
    assert e == decimal.Decimal('0.740100')
