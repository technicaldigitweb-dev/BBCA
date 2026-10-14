"""High-priority Buy Box loss alerts.

Every one of these must hold before a notification is generated:

  1. the ASIN is high-priority under an APPROVED rule
  2. current ownership is VERIFIED as NO (verification_status == 'live')
  3. a previous reliable check established we HELD the Buy Box (a real transition)
  4. the alert is not a duplicate
  5. an approved channel and recipient are configured

Rule 2 is the important one: a stale historical 0% reading is explicitly NOT a loss
event. The ten-ASIN sample found 3 of 10 such readings where we actually still held
the Buy Box, so alerting on them would have produced false alarms.

Nothing is transmitted unless dry_run=False AND the alert_delivery_approved gate is
set. There is no code path that sends on a default.
"""
from __future__ import annotations

import datetime as dt
import json

import config
from history import History


class AlertEngine:
    def __init__(self, hist: History | None = None, log=print):
        self.h = hist or History()
        self.log = log

    # --- priority -----------------------------------------------------------
    def priority_rule(self) -> tuple[bool, str, set]:
        """Approved high-priority ASIN set. Returns (approved, explanation, asins)."""
        if not config.gate('priority_rule_approved'):
            return False, ('No approved high-priority rule. Candidate source: '
                           f'{config.PRIORITY_SOURCE_CANDIDATE} '
                           f'(proposed values {config.PRIORITY_VALUES_CANDIDATE}) '
                           '- NOT approved, so no ASIN is treated as high-priority.'), set()
        over = config.load_overrides().get('priority_asins')
        if over:
            return True, 'operator-supplied approved ASIN list', set(over)
        return False, 'priority_rule_approved is set but no approved ASIN list is configured', set()

    # --- trigger ------------------------------------------------------------
    def evaluate(self, run_id: str) -> dict:
        """Decide which results in a run qualify. Pure decision - sends nothing."""
        approved, why, priority_asins = self.priority_rule()
        results = [r for r in self.h.latest_results() if r['run_id'] == run_id]
        candidates, rejected = [], []

        for r in results:
            reasons = []
            if r['buy_box_status'] != 'NO':
                reasons.append(f"status is {r['buy_box_status']}, not NO")
            if r.get('verification_status') != 'live':
                reasons.append(f"ownership is {r.get('verification_status')} "
                               "- a stale historical reading is not a loss event")
            if not approved:
                reasons.append('no approved high-priority rule')
            elif r['asin'] not in priority_asins:
                reasons.append('ASIN is not high-priority')

            prev = self.h.previous_status(r['asin'], r['seller_account'],
                                          r['marketplace'], run_id)
            if prev is None:
                reasons.append('no previous check - cannot establish a loss transition')
            elif prev['buy_box_status'] != 'YES':
                reasons.append(f"previous status was {prev['buy_box_status']}, not YES "
                               "- no transition")
            elif prev.get('verification_status') not in ('live', 'historical'):
                reasons.append('previous check is not reliable')

            key = self.alert_key(r)
            if self.h.alert_already_sent(key):
                reasons.append('duplicate - already alerted')

            if reasons:
                rejected.append({'asin': r['asin'], 'marketplace': r['marketplace'],
                                 'why_not': reasons})
            else:
                candidates.append({'result': r, 'previous': prev, 'alert_key': key})

        channel_ok, channel_why = self.channel_ready()
        return {'run_id': run_id, 'priority_rule_approved': approved, 'priority_detail': why,
                'channel_ready': channel_ok, 'channel_detail': channel_why,
                'candidates': candidates, 'rejected': rejected,
                'evaluated': len(results)}

    @staticmethod
    def alert_key(r: dict) -> str:
        day = (r.get('checked_at') or '')[:10]
        return f"{r['asin']}|{r['seller_account']}|{r['marketplace']}|{day}"

    def channel_ready(self) -> tuple[bool, str]:
        if not config.gate('alert_delivery_approved'):
            return False, 'alert_delivery_approved gate is not set'
        over = config.load_overrides()
        ch = over.get('alert_channel') or config.ALERT_CHANNEL
        rcpt = over.get('alert_recipients') or config.ALERT_RECIPIENTS
        if not ch:
            return False, 'no alert channel configured'
        if not rcpt:
            return False, 'no recipients configured'
        return True, f'{ch} -> {len(rcpt)} recipient(s)'

    # --- payload ------------------------------------------------------------
    @staticmethod
    def build_payload(c: dict) -> dict:
        r, prev = c['result'], c['previous']
        return {
            'asin': r['asin'], 'sku': r.get('sku'),
            'seller_account': r['seller_account'], 'seller_id': r.get('seller_id'),
            'marketplace': r['marketplace'],
            'previous_status': prev['buy_box_status'] if prev else None,
            'previous_checked_at': prev.get('checked_at') if prev else None,
            'current_status': r['buy_box_status'],
            'possible_reason': json.loads(r.get('possible_reason') or '[]'),
            'official_reason': r.get('official_reason'),
            'checked_at': r.get('checked_at'),
            'evidence_source': r.get('evidence_source'),
            'dashboard': str(config.OUTPUT / '2026-10-14_tharsi_buy_box_monitor_v003.html'),
        }

    @staticmethod
    def render(p: dict) -> str:
        return (f"Buy Box lost - {p['asin']} ({p['marketplace']})\n"
                f"  SKU            : {p.get('sku') or '-'}\n"
                f"  Account        : {p['seller_account']} ({p.get('seller_id') or 'no token'})\n"
                f"  Previous       : {p['previous_status']} at {p['previous_checked_at']}\n"
                f"  Current        : {p['current_status']} at {p['checked_at']}\n"
                f"  Possible reason: {', '.join(p['possible_reason']) or '-'}\n"
                f"  Official reason: {p['official_reason']}\n"
                f"  Evidence       : {p['evidence_source']}\n"
                f"  Dashboard      : {p['dashboard']}")

    # --- dispatch -----------------------------------------------------------
    def dispatch(self, run_id: str, dry_run: bool | None = None) -> dict:
        dry_run = config.ALERT_DRY_RUN_DEFAULT if dry_run is None else dry_run
        ev = self.evaluate(run_id)
        sent, suppressed = [], []

        if not dry_run and not ev['channel_ready']:
            # Refuse to send rather than fall back to a default channel.
            self.log(f"ALERTS: live send refused - {ev['channel_detail']}")
            dry_run = True
            suppressed.append('live send refused: ' + ev['channel_detail'])

        for c in ev['candidates']:
            payload = self.build_payload(c)
            text = self.render(payload)
            if dry_run:
                self.log('--- DRY RUN ALERT (not transmitted) ---\n' + text)
            else:
                raise NotImplementedError(
                    'No delivery transport is implemented. A channel must be approved and '
                    'wired explicitly - this engine will not invent one.')
            self.h.record_alert(c['alert_key'], run_id,
                                {'asin': payload['asin'],
                                 'seller_account': payload['seller_account'],
                                 'marketplace': payload['marketplace']},
                                config.ALERT_CHANNEL or 'dry-run', dry_run, payload)
            sent.append(payload)

        return {'run_id': run_id, 'dry_run': dry_run, 'alerted': len(sent),
                'rejected': len(ev['rejected']), 'evaluated': ev['evaluated'],
                'priority_rule_approved': ev['priority_rule_approved'],
                'priority_detail': ev['priority_detail'],
                'channel_ready': ev['channel_ready'], 'channel_detail': ev['channel_detail'],
                'payloads': sent, 'suppressed': suppressed,
                'rejection_sample': ev['rejected'][:5]}
