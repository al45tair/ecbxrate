import datetime

try:
    import cdecimal as decimal
except ImportError:
    import decimal

from sqlalchemy.engine import Engine, Connection
from sqlalchemy import create_engine
from sqlalchemy.sql import select, exists, func, and_, or_, not_

import urllib2
import datetime
import re

from lxml import etree

from .tables import exchange_rates, info

DAILY_URL = 'http://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml'
HISTORIC_URL = 'http://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml'
HISTORIC_URL_90 = 'http://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist-90.xml'
CUBE_TAG = '{http://www.ecb.int/vocabulary/2002-08-01/eurofxref}Cube'

_date_re = re.compile(r'^([0-9]{4,})-([0-9]{2})-([0-9]{2})$')

class ExchangeRateStore(object):
    def __init__(self, ecu):
        self.connection = None
        self.owns_connection = True

        if isinstance(ecu, Engine):
            self.engine = ecu
        elif isinstance(ecu, Connection):
            self.engine = ecu.engine
            self.connection = ecu
            self.owns_connection = False
        else:
            self.engine = create_engine(ecu)

    def _connect(self):
        if self.connection:
            return self.connection
        self.connection = self.engine.connect()
        return self.connection

    def _disconnect(self):
        if self.owns_connection:
            self.connection.close()
            self.connection = None

    def get_rate(self, from_currency, to_currency, as_of_date=None,
                 closest_rate=False):
        """Returns the exchange rate pair (date, E), such that

                to_amount = from_amount * E

           where to_amount is expressed in to_currency and from_amount in
           from_currency.

           If ``as_of_date`` is specified, returns the rate published for the
           date specified.  You can also specify 'today' or 'yesterday' or
           'latest' for this parameter.

           If you specify a date and are happy with the latest rate known
           prior to that date, you can set ``closest_rate`` to True.

           If no exchange rate is known for the combination you have
           specified, this method returns (date, None)."""

        if as_of_date is None or as_of_date == 'today':
            as_of_date = datetime.date.today()
        if as_of_date == 'yesterday':
            as_of_date = datetime.date.today() - datetime.timedelta(days=1)

        er1 = exchange_rates.alias()
        er2 = exchange_rates.alias()

        if from_currency == 'EUR':
            from_rate = decimal.Decimal(1)
            if to_currency == 'EUR':
                to_rate = decimal.Decimal(1)
                stmt = None
            else:
                stmt = select([func.max(er2.c.date).label('date'),
                               er2.c.rate.label('to_rate')]) \
                  .where(er2.c.currency==to_currency)
                er = er2
        else:
            if to_currency == 'EUR':
                to_rate = decimal.Decimal(1)
                stmt = select([func.max(er1.c.date).label('date'),
                               er1.c.rate.label('from_rate')]) \
                  .where(er1.c.currency==from_currency)
                er = er1
            else:
                stmt = select([func.max(er1.c.date).label('date'),
                               er1.c.rate.label('from_rate'),
                               er2.c.rate.label('to_rate')]) \
                    .where(and_(er1.c.date==er2.c.date,
                                er1.c.currency==from_currency,
                                er2.c.currency==to_currency))
                er = er1

        if stmt is not None:
            if as_of_date != 'latest':
                if closest_rate:
                    stmt = stmt.where(er.c.date<=as_of_date)
                else:
                    stmt = stmt.where(er.c.date==as_of_date)
            
            conn = self._connect()
            try:
                with conn.begin() as trans:
                    result = conn.execute(stmt).fetchone()

                    if result is None or result == (None, None, None):
                        return (as_of_date, None)

                    if from_currency != 'EUR':
                        from_rate = result['from_rate']
                    if to_currency != 'EUR':
                        to_rate = result['to_rate']

                    rate_date = result['date']
            finally:
                self._disconnect()
        else:
            rate_date = datetime.date.today()
            
        with decimal.localcontext() as ctx:
            rate = to_rate / from_rate

        # If we have fewer than 6dp, round to 6dp; if we have more than 6dp
        # and the number has significant figures to the left of the decimal
        # point, round to 6dp.  Otherwise, round to 6sf.
        exp = rate.as_tuple().exponent
        if exp > -6:
            q = decimal.Decimal('0.000001')
            rate = rate.quantize(q)
        elif exp < -6:
            adj = rate.adjusted()
            if adj < 0:
                q = decimal.Decimal((0,[1],adj-5))
            else:
                q = decimal.Decimal((0,[1],-6))
            rate = rate.quantize(q)
        
        return (rate_date, rate)

    def _parse_xml(self, xmlfile, days=None):
        rates = []
        date_count = 0
        current_date = None
        max_date = None
        
        for event, element in etree.iterparse(xmlfile, events=('start', 'end')):
            if element.tag != CUBE_TAG:
                continue
                
            if event == 'start' and element.tag == CUBE_TAG:
                time = element.get('time', None)
                if time:
                    m = _date_re.match(time)
                    current_date = datetime.date(int(m.group(1)),
                                                 int(m.group(2)),
                                                 int(m.group(3)))

                    if max_date is None or max_date < current_date:
                        max_date = current_date
                    
                    if days and date_count + 1 > days:
                        break
                    
                    date_count += 1

            if event == 'end' and element.tag == CUBE_TAG:
                currency = element.get('currency', None)
                rate = element.get('rate', None)

                if currency and rate:
                    rate = decimal.Decimal(rate)

                    rates.append({ 'date': current_date,
                                   'currency': currency,
                                   'rate': rate })
                    
        return (rates, date_count, max_date)
    
    def initialise(self, days=None):
        """Initialise the exchange rate store from historic data."""
        url = HISTORIC_URL
        if days and days <= 90:
            url = HISTORIC_URL_90
            
        # Parse the historic XML to load the data
        f = urllib2.urlopen(url)
        try:
            rates, date_count, current_date = self._parse_xml(f, days)
        finally:
            f.close()
            
        # Create the tables if required
        exchange_rates.create(self.engine, checkfirst=True)
        info.create(self.engine, checkfirst=True)
        
        # Save it
        conn = self._connect()
        try:
            with conn.begin() as trans:
                conn.execute(exchange_rates.delete())
                conn.execute(exchange_rates.insert(), *rates)
                conn.execute(info.delete())
                conn.execute(info.insert(), { 'last_update': current_date })
        finally:
            self._disconnect()

        return (len(rates), date_count)
    
    def update(self):
        """Update the exchange rate store with the latest data, from the ECB's
        daily feed.  Since the daily feed contains only the most recent day's
        exchange rates, this needs to be called at least one a day, after
        3pm CET, in order to keep the store up to date.  If the store gets
        out of date, you will need to call ``initialise`` again."""
        rates = []
        current_date = None
        date_count = 0
        
        # Parse the XML to load the data
        f = urllib2.urlopen(DAILY_URL)
        try:
            rates, date_count, current_date = self._parse_xml(f)
        finally:
            f.close()
            
        # Save it
        conn = self._connect()
        try:
            with conn.begin() as trans:
                conn.execute(exchange_rates.delete()\
                             .where(exchange_rates.c.date == current_date))
                conn.execute(exchange_rates.insert(), *rates)
                conn.execute(info.update(), { 'last_update': current_date })
        finally:
            self._disconnect()

        return (len(rates), current_date)

    def last_updated(self):
        """Return the date for the most recent updates."""
        conn = self._connect()
        try:
            with conn.begin() as trans:
                return conn.execute(select([info.c.last_update]))\
                  .fetchone()[info.c.last_update]
        finally:
            self._disconnect
