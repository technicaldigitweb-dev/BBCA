"""Derive build_html_v003.py from build_html_v002.py.

v003 adds the live-check layer on top of v002, keeping the same UI:
  * live_status held SEPARATELY from the historical status (never overwrites it)
  * a Live Check column + filter, and a conflict flag
  * summary cards for live-checked / conflicts
  * a seller-identity banner (tokens VERIFIED) and a stale-data warning
  * drawer section showing the live evidence with its own timestamp

Run this, then run build_html_v003.py.
"""
import io
import os

S = os.path.dirname(os.path.abspath(__file__))
src = io.open(os.path.join(S, 'build_html_v002.py'), encoding='utf-8').read()
orig_len = len(src)


def sub(old, new, why):
    global src
    assert old in src, 'PATCH TARGET MISSING (%s): %s' % (why, old[:70])
    assert src.count(old) == 1, 'PATCH TARGET AMBIGUOUS (%s)' % why
    src = src.replace(old, new, 1)


# ---------------------------------------------------------------- python side
sub("OUT = r'C:\\Users\\LED 222\\Buy_Box_Check_Automation_Tharsi\\05_OUTPUT\\2026-10-14_tharsi_buy_box_monitor_v002.html'",
    "OUT = r'C:\\Users\\LED 222\\Buy_Box_Check_Automation_Tharsi\\05_OUTPUT\\2026-10-14_tharsi_buy_box_monitor_v003.html'",
    'output path')

sub("rows, summary, hist = load('dashboard_rows_v002'), load('summary'), load('bb_history_daily')",
    "rows, summary, hist = load('dashboard_rows_v003'), load('summary_v003'), load('bb_history_daily')",
    'inputs')

sub("summary['version'] = 'v002'", "summary['version'] = 'v003'", 'version')

sub("""  .card.a::before{background:var(--amber)} .card.n::before{background:var(--grey)}""",
    """  .card.a::before{background:var(--amber)} .card.n::before{background:var(--grey)}
  .banner{background:#fff;border:1px solid var(--line);border-left:5px solid var(--green);
          border-radius:6px;padding:12px 18px;margin-bottom:14px;font-size:13px}
  .banner.warn{border-left-color:var(--amber);background:#fffdf5}""",
    'v003 css')

sub("""  <div class="notice" id="notice"></div>""",
    """  <div class="banner" id="bSeller"></div>
  <div class="banner warn" id="bStale"></div>
  <div class="notice" id="notice"></div>""",
    'v003 banners')

# --- live pill rendering in the table

io.open(os.path.join(S, 'build_html_v003.py'), 'w', encoding='utf-8').write(src)
print('build_html_v003.py written  (%d -> %d chars, +%d)' % (orig_len, len(src), len(src) - orig_len))
