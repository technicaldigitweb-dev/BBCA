"""Local backend for the dashboard's Run Check button.

Standard-library http.server only - no framework dependency, no secrets in the page.
Binds to 127.0.0.1 by default: this is an operator tool, not a public service.

    python api.py [--port 8787] [--host 127.0.0.1]

Endpoints
    GET  /api/buy-box/health
    POST /api/buy-box/check          {"asin","account","marketplace","live":bool}
    POST /api/buy-box/check-all      {"live":bool}            - starts a background run
    GET  /api/buy-box/runs/<run_id>
    GET  /api/buy-box/results/latest?limit=N
    GET  /api/buy-box/history?asin=&account=&marketplace=
    GET  /api/buy-box/daily?days=14

The dashboard stays a standalone offline file. It probes /health; if the backend is
absent the Run Check button says so plainly instead of pretending. Credentials are read
from the environment inside this process and are never sent to the browser.
"""
from __future__ import annotations

import argparse
import json
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

import config
import sources
from engine import Engine, RunLocked
from history import History

_RUNS: dict[str, dict] = {}       # run_id -> {"state": ..., "detail": ...}
_LOCK = threading.Lock()


def _bg_full(live: bool) -> str:
    h = History()
    eng = Engine(h, log=lambda m: None)
    run_id = None

    def work():
        nonlocal run_id
        try:
            res = eng.run('manual_full', prefer_live=live)
            with _LOCK:
                _RUNS[res['run_id']] = {'state': res['status'], 'detail': res}
        except (RunLocked, sources.SourceUnavailable) as e:
            with _LOCK:
                _RUNS[run_id or 'pending'] = {'state': 'failed', 'detail': str(e)}
        except Exception as e:
            with _LOCK:
                _RUNS[run_id or 'pending'] = {'state': 'failed', 'detail': repr(e)}

    t = threading.Thread(target=work, daemon=True)
    t.start()
    return 'started'


class Handler(BaseHTTPRequestHandler):
    server_version = 'BuyBoxCheck/1.0'

    def log_message(self, fmt, *args):      # quieter default logging
        pass

    def _send(self, code: int, payload: dict):
        body = json.dumps(payload, default=str).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        # The dashboard is opened from file://, whose Origin is "null".
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(204, {})

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        h = History()
        try:
            if u.path == '/api/buy-box/health':
                src_state = {n: dict(zip(('available', 'detail'), s.available()))
                             for n, s in sources.REGISTRY.items()}
                last = h.last_successful_run()
                return self._send(200, {
                    'ok': True, 'sources': src_state,
                    'gates': {g: config.gate(g) for g in config.GATES},
                    'schedule': {'cron': config.SCHEDULE_CRON,
                                 'timezone': config.SCHEDULE_TIMEZONE,
                                 'approved': config.gate('daily_schedule_approved')},
                    'last_successful_run': last})

            if u.path.startswith('/api/buy-box/runs/'):
                rid = u.path.rsplit('/', 1)[-1]
                run = h.get_run(rid)
                with _LOCK:
                    mem = _RUNS.get(rid)
                if not run and not mem:
                    return self._send(404, {'error': 'unknown run_id'})
                return self._send(200, {'run': run, 'progress': mem})

            if u.path == '/api/buy-box/results/latest':
                lim = int(q.get('limit', ['500'])[0])
                return self._send(200, {'results': h.latest_results(lim)})

            if u.path == '/api/buy-box/history':
                asin = q.get('asin', [''])[0]
                acct = q.get('account', [''])[0]
                mkt = q.get('marketplace', [''])[0]
                if not (asin and acct and mkt):
                    return self._send(400, {'error': 'asin, account and marketplace are required'})
                return self._send(200, {'history': h.history_for(asin, acct, mkt)})

            if u.path == '/api/buy-box/daily':
                return self._send(200, {'daily': h.daily_history(int(q.get('days', ['14'])[0]))})

            return self._send(404, {'error': 'unknown endpoint'})
        except Exception:
            return self._send(500, {'error': traceback.format_exc(limit=2)})
        finally:
            h.close()

    def do_POST(self):
        u = urlparse(self.path)
        try:
            n = int(self.headers.get('Content-Length') or 0)
            body = json.loads(self.rfile.read(n) or b'{}')
        except Exception:
            return self._send(400, {'error': 'invalid JSON body'})

        try:
            if u.path == '/api/buy-box/check':
                for k in ('asin', 'account', 'marketplace'):
                    if not body.get(k):
                        return self._send(400, {'error': f'{k} is required'})
                h = History()
                try:
                    res = Engine(h, log=lambda m: None).check_single(
                        body['asin'], body['account'], body['marketplace'],
                        prefer_live=bool(body.get('live', True)))
                    return self._send(200, res)
                except sources.SourceUnavailable as e:
                    return self._send(503, {'error': 'no live ownership source available',
                                            'detail': str(e)})
                except RunLocked as e:
                    return self._send(409, {'error': str(e)})
                finally:
                    h.close()

            if u.path == '/api/buy-box/check-all':
                state = _bg_full(bool(body.get('live', False)))
                return self._send(202, {'state': state,
                                        'note': 'poll /api/buy-box/runs/<run_id> or '
                                                '/api/buy-box/results/latest'})

            return self._send(404, {'error': 'unknown endpoint'})
        except Exception:
            return self._send(500, {'error': traceback.format_exc(limit=2)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', type=int, default=8787)
    ap.add_argument('--host', default='127.0.0.1')
    a = ap.parse_args()
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    print(f'Buy Box check backend on http://{a.host}:{a.port}  (Ctrl-C to stop)', flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
