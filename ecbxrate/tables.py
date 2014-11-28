import sqlalchemy
from sqlalchemy import *

try:
    import cdecimal as decimal
except ImportError:
    import decimal

metadata = MetaData()

class ExchangeRate(sqlalchemy.types.TypeDecorator):
    impl = sqlalchemy.types.BigInteger

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return int(value * 10**6)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return decimal.Decimal(value) / 10**6

exchange_rates = Table('ecbxrate', metadata,
                       Column('date', Date),
                       Column('currency', String(3)),
                       Column('rate', ExchangeRate)
                       )

info = Table('ecbxrate_info', metadata,
             Column('last_update', Date))
