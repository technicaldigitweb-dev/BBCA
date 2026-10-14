"""Approved-source adapters for Buy Box ownership.

One interface, several backings. The point of the abstraction is that an unavailable
source reports itself as unavailable instead of being silently replaced by a weaker
one. Nothing here ever converts a historical report into a live ownership claim.

Verification states
-------------------
    YES           ownership verified as ours
    NO            ownership verified as not ours
    NOT VERIFIED  ownership could not be determined from available evidence
    CHECK ERROR   a technical or access problem prevented the check

Timestamps are kept distinct and are never substituted for one another:
    source_observed_at  when the SOURCE observed the fact (e.g. report date)
    checked_at          when THIS run executed the check
    live_verified_at    when live ownership was confirmed (None unless truly live)
"""
from __future__ import annotations

import datetime as dt
import os
from dataclasses import dataclass, field, asdict

import config


@dataclass
class CheckResult:
    asin: str
    seller_account: str
    marketplace: str
    buy_box_status: str                  # YES | NO | NOT VERIFIED | CHECK ERROR
    verification_status: str             # historical | live | unavailable | error
    evidence_source: str
    source_observed_at: str | None = None
    checked_at: str | None = None
    live_verified_at: str | None = None
    official_reason: str = 'Unknown'
    possible_reason: list[str] = field(default_factory=list)
    seller_id: str | None = None
    sku: str | None = None
    stock_quantity: int | None = None
    listing_status: str | None = None
    error_code: str | None = None
    detail: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


class SourceUnavailable(Exception):
    """Raised when a source cannot answer and must not be silently substituted."""


class BuyBoxSource:
    """Adapter interface. Implementations must not fabricate ownership."""

    name = 'abstract'
    gives_live_ownership = False

    def available(self) -> tuple[bool, str]:
        raise NotImplementedError

    def check(self, record: dict) -> CheckResult:
        raise NotImplementedError

    def check_batch(self, records: list[dict]) -> list[CheckResult]:
        return [self.check(r) for r in records]


def _now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec='seconds')


# ---------------------------------------------------------------------------
class HistoricalReportSource(BuyBoxSource):
    """ledsone.business_reports.amz_sales_and_traffic_by_asin.buy_box_percentage

    This is HISTORICAL day-level evidence, not current ownership. It is marked
    verification_status='historical' and never sets live_verified_at.
    """

    name = 'historical_report'
    gives_live_ownership = False

    def __init__(self, window_days: int | None = None):
        self.window_days = window_days or config.REPORT_WINDOW_DAYS
        self._cache: dict | None = None

    def available(self) -> tuple[bool, str]:
        if not config.source_db_available():
            return False, f'${config.SOURCE_DB_ENV} is not set'
        return True, 'ok'

    def load(self) -> dict:
        """One query for the whole run - per-ASIN queries would be 20k round trips."""
        if self._cache is not None:
            return self._cache
        ok, why = self.available()
        if not ok:
            raise SourceUnavailable(why)
        import psycopg
        mp_of = {v: k for k, v in config.MARKETPLACES.items()}
        ss_of = {v: k for k, v in config.ACCOUNTS.items()}
        with psycopg.connect(config.source_db_dsn(),
                             connect_timeout=config.REQUEST_TIMEOUT_S) as c, c.cursor() as cur:
            cur.execute('SET TRANSACTION READ ONLY')
            cur.execute("""
              SELECT max(date) FROM business_reports.amz_sales_and_traffic_by_asin
              WHERE sub_source = ANY(%s) AND market_place = ANY(%s)
            """, (list(ss_of.values()), list(mp_of.values())))
            max_date = cur.fetchone()[0]
            cur.execute("""
              SELECT DISTINCT ON (child_asin, sub_source, market_place)
                     child_asin, sub_source, market_place, date, buy_box_percentage
              FROM business_reports.amz_sales_and_traffic_by_asin
              WHERE sub_source = ANY(%s) AND market_place = ANY(%s)
                AND date > %s::date - %s AND date <= %s::date
              ORDER BY child_asin, sub_source, market_place, date DESC
            """, (list(ss_of.values()), list(mp_of.values()), max_date,
                  self.window_days, max_date))
            self._cache = {
                (a, config.ACCOUNTS[s], config.MARKETPLACES[m]): (d, float(p) if p is not None else None)
                for a, s, m, d, p in cur.fetchall()
            }
        self._max_date = max_date
        return self._cache

    def check(self, record: dict) -> CheckResult:
        now = _now()
        key = (record['asin'], record['seller_account'], record['marketplace'])
        base = dict(asin=record['asin'], seller_account=record['seller_account'],
                    marketplace=record['marketplace'], sku=record.get('sku'),
                    stock_quantity=record.get('stock'), listing_status=record.get('listing_status'),
                    seller_id=config.SELLER_IDS.get(record['seller_account']),
                    evidence_source=f'{config.SOURCE_DB_NAME}.business_reports.'
                                    f'amz_sales_and_traffic_by_asin.buy_box_percentage',
                    checked_at=now)
        try:
            hit = self.load().get(key)
        except SourceUnavailable as e:
            return CheckResult(buy_box_status='CHECK ERROR', verification_status='error',
                               error_code='SOURCE_UNAVAILABLE', detail=str(e), **base)

        if hit is None:
            return CheckResult(buy_box_status='NOT VERIFIED', verification_status='historical',
                               detail=f'No report row within {self.window_days} days of '
                                      f'{self._max_date}', **base)
        obs, pct = hit
        base['source_observed_at'] = str(obs)
        if pct == 100:
            return CheckResult(buy_box_status='YES', verification_status='historical',
                               detail=f'Buy Box held for 100% of page views on {obs}', **base)
        if pct == 0:
            return CheckResult(buy_box_status='NO', verification_status='historical',
                               official_reason='Unknown', **base,
                               detail=f'Buy Box held for 0% of page views on {obs}')
        return CheckResult(buy_box_status='NOT VERIFIED', verification_status='historical',
                           detail=f'Split ownership {pct}% on {obs} - no approved threshold',
                           **base)


# ---------------------------------------------------------------------------
class SpApiPricingSource(BuyBoxSource):
    """SP-API Product Pricing (getItemOffers) - the correct source for LIVE ownership.

    Not wired up: the estate's SP-API credentials live in the application tier and are
    not reachable here (see 06_EVIDENCE/bulk_automation_readiness_v2.md). The adapter
    exists so the engine is ready the moment access is granted, and so that until then
    it reports a transparent blocked state rather than falling back to historical data.
    """

    name = 'spapi_product_pricing'
    gives_live_ownership = True

    def available(self) -> tuple[bool, str]:
        if not config.gate('live_ownership_source_approved'):
            return False, ('SP-API Product Pricing access is not approved '
                           '(gate: live_ownership_source_approved)')
        for var in ('SPAPI_REFRESH_TOKEN', 'SPAPI_CLIENT_ID', 'SPAPI_CLIENT_SECRET'):
            if not os.environ.get(var):
                return False, f'${var} is not set'
        return True, 'ok'

    def check(self, record: dict) -> CheckResult:
        ok, why = self.available()
        return CheckResult(
            asin=record['asin'], seller_account=record['seller_account'],
            marketplace=record['marketplace'], sku=record.get('sku'),
            buy_box_status='CHECK ERROR', verification_status='unavailable',
            evidence_source=self.name, checked_at=_now(),
            error_code='INTEGRATION_NOT_AVAILABLE', detail=why)


# ---------------------------------------------------------------------------
class LiveBrowserSource(BuyBoxSource):
    """Live Amazon product page via an operator-opened browser (CDP).

    Proven for single-ASIN and small batches (06_EVIDENCE/phase4_5_ten_asin_verification.md).
    Deliberately capped: Amazon serves an automation interstitial under volume, and the
    project forbids bypassing it. The cap is a refusal, not a retry.
    """

    name = 'live_browser_cdp'
    gives_live_ownership = True
    MAX_RECORDS = 25

    def available(self) -> tuple[bool, str]:
        import urllib.request
        try:
            urllib.request.urlopen('http://127.0.0.1:9222/json/version', timeout=4).read()
        except Exception:
            return False, 'no CDP browser on 127.0.0.1:9222 (start Chrome with --remote-debugging-port=9222)'
        return True, 'ok'

    def check_batch(self, records: list[dict]) -> list[CheckResult]:
        if len(records) > self.MAX_RECORDS:
            raise SourceUnavailable(
                f'{len(records)} records exceeds the {self.MAX_RECORDS}-record cap for browser '
                'checking. Bulk browser collection is not authorised - use SP-API.')
        return [self.check(r) for r in records]

    def check(self, record: dict) -> CheckResult:
        ok, why = self.available()
        base = dict(asin=record['asin'], seller_account=record['seller_account'],
                    marketplace=record['marketplace'], sku=record.get('sku'),
                    evidence_source=self.name, checked_at=_now())
        if not ok:
            return CheckResult(buy_box_status='CHECK ERROR', verification_status='unavailable',
                               error_code='BROWSER_UNAVAILABLE', detail=why, **base)
        try:
            import sys
            sys.path.insert(0, str(config.ROOT / '03_SCRIPTS'))
            import verify_live_listing as V
            from playwright.sync_api import sync_playwright
        except Exception as e:
            return CheckResult(buy_box_status='CHECK ERROR', verification_status='error',
                               error_code='IMPORT_FAILED', detail=str(e)[:150], **base)

        with sync_playwright() as p:
            b = p.chromium.connect_over_cdp('http://127.0.0.1:9222', timeout=30000)
            ctx = b.contexts[0]
            page = ctx.new_page()
            page.set_default_navigation_timeout(60000)
            try:
                ok_loc, detail = V.setup_uk(ctx, page)
                if not ok_loc:
                    code = 'ACCESS_CONTROL' if detail.startswith('BLOCKED') else 'LOCALE_UNCONFIRMED'
                    return CheckResult(buy_box_status='CHECK ERROR',
                                       verification_status='unavailable',
                                       error_code=code, detail=detail, **base)
                res = V.check_asin(page, {'asin': record['asin'],
                                          'account': record['seller_account']})
            finally:
                page.close()

        if res.get('blocked_markers'):
            return CheckResult(buy_box_status='CHECK ERROR', verification_status='unavailable',
                               error_code='ACCESS_CONTROL',
                               detail='Amazon access control present; halted without interacting',
                               **base)

        now = _now()
        offers = (res.get('offers') or {}).get('list') or []
        our_token = config.SELLER_IDS.get(record['seller_account'])
        our_on_page = [o for o in offers if o.get('seller_id') == our_token]
        featured = (res.get('featured_seller_name') or '').strip()
        feat_u = featured.upper()
        acct_u = record['seller_account'].upper()
        feat_is_ours = feat_u.replace(' ', '') == acct_u.replace(' ', '')

        base.update(seller_id=our_token, source_observed_at=now, live_verified_at=now,
                    stock_quantity=record.get('stock'),
                    listing_status=record.get('listing_status'))

        if not featured and res.get('out_of_stock_block'):
            return CheckResult(buy_box_status='NO', verification_status='live',
                               possible_reason=[f"Listing unavailable: "
                                                f"{(res.get('availability') or '')[:70]}"], **base)
        if not featured:
            return CheckResult(buy_box_status='NOT VERIFIED', verification_status='live',
                               detail='No featured seller readable from the page', **base)
        if feat_is_ours and our_on_page:
            return CheckResult(buy_box_status='YES', verification_status='live',
                               possible_reason=[f'Our account holds the featured offer '
                                                f'(verified token {our_token})'], **base)
        if feat_is_ours:
            return CheckResult(buy_box_status='NOT VERIFIED', verification_status='live',
                               detail='Featured seller name matches our account but no '
                                      'verified token was present on the page', **base)
        if feat_u in {g.upper() for g in config.GROUP_ACCOUNTS}:
            return CheckResult(buy_box_status='NO', verification_status='live',
                               possible_reason=[f'Featured offer held by {featured} '
                                                f'- our own group company'], **base)
        return CheckResult(buy_box_status='NO', verification_status='live',
                           possible_reason=[f'Featured offer held by {featured} '
                                            f'(display name only, no token exposed)'], **base)


REGISTRY = {s.name: s for s in (HistoricalReportSource(), SpApiPricingSource(), LiveBrowserSource())}


def resolve(prefer_live: bool) -> tuple[BuyBoxSource, list[str]]:
    """Pick a source. A live request never silently degrades to historical data."""
    notes = []
    if prefer_live:
        for name in ('spapi_product_pricing', 'live_browser_cdp'):
            src = REGISTRY[name]
            ok, why = src.available()
            if ok:
                return src, notes
            notes.append(f'{name}: {why}')
        raise SourceUnavailable('No live ownership source is available. ' + ' | '.join(notes))
    src = REGISTRY['historical_report']
    ok, why = src.available()
    if not ok:
        raise SourceUnavailable(f'historical_report: {why}')
    return src, notes
