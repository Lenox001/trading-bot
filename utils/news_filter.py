import datetime
import logging
import requests
from bs4 import BeautifulSoup
import re

class NewsFilter:
    def __init__(self, quiet_minutes=30):
        self.quiet_minutes = quiet_minutes
        self.logger = logging.getLogger('NewsFilter')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _fetch_high_impact_events(self):
        """
        Fetch today's high‑impact events from ForexFactory.
        Returns a list of dicts with 'time' (datetime) and 'currency'.
        """
        today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
        url = f"https://www.forexfactory.com/calendar?day={today}"
        try:
            resp = self.session.get(url, timeout=10)
            resp.raise_for_status()
            # Use built-in html.parser – no lxml needed
            soup = BeautifulSoup(resp.content, 'html.parser')
            events = []
            rows = soup.select('tr.calendar_row')
            for row in rows:
                # Impact: red folder = high impact
                impact_elem = row.select_one('td.impact span')
                if not impact_elem:
                    continue
                # 'high' class indicates red-folder news
                if 'high' not in impact_elem.get('class', []):
                    continue
                # Time
                time_elem = row.select_one('td.time')
                if not time_elem:
                    continue
                time_str = time_elem.get_text(strip=True)
                if not time_str or time_str.lower() == 'all day':
                    continue
                # Currency
                currency_elem = row.select_one('td.currency')
                if not currency_elem:
                    continue
                currency = currency_elem.get_text(strip=True)
                if not currency:
                    continue
                # Parse time (ForexFactory times are US Eastern Time)
                try:
                    t = datetime.datetime.strptime(time_str, "%I:%M%p")
                    event_time = datetime.datetime.combine(
                        datetime.datetime.utcnow().date(), t.time()
                    )
                    # Convert ET to UTC: ET is UTC-4 (simplified, close enough)
                    event_time = event_time + datetime.timedelta(hours=4)
                except ValueError:
                    continue

                events.append({
                    'time': event_time,
                    'currency': currency
                })
            return events
        except Exception as e:
            self.logger.error(f"Failed to fetch ForexFactory calendar: {e}")
            return []

    def is_news_quiet(self, symbol):
        """
        Returns False if a high‑impact event for one of the symbol's currencies
        falls within the quiet window.
        """
        try:
            now = datetime.datetime.utcnow()
            start = now - datetime.timedelta(minutes=self.quiet_minutes)
            end = now + datetime.timedelta(minutes=self.quiet_minutes)

            # Extract currencies from symbol (e.g. EURUSD → EUR, USD)
            if len(symbol) == 6:
                currencies = [symbol[:3], symbol[3:6]]
            else:
                currencies = [symbol[:3]]

            events = self._fetch_high_impact_events()
            for event in events:
                if event['currency'] in currencies and start <= event['time'] <= end:
                    self.logger.info(
                        f"High impact news in quiet window: {event['currency']} at {event['time']}"
                    )
                    return False
            return True
        except Exception as e:
            self.logger.error(f"News check error: {e}")
            # On error, allow trading to avoid unnecessary downtime
            return True