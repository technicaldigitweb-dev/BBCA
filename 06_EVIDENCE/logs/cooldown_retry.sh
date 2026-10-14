#!/bin/sh
# Characterise whether the Amazon automation interstitial is a timed cooldown.
# Read-only; no click-through, no fingerprint spoofing.
LOG="06_EVIDENCE/logs/cooldown_retry.log"
echo "start $(date -Is)" > "$LOG"
for wait in 300 600 900; do
  sleep $wait
  echo "--- after ${wait}s cumulative pause, $(date -Is) ---" >> "$LOG"
  PYTHONIOENCODING=utf-8 timeout 100 python /tmp/diag_headed.py headless >> "$LOG" 2>&1
  curl -s --max-time 25 -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36" \
       "https://www.amazon.co.uk/dp/B086385W3W" -o /tmp/cc.html
  echo "curl_bytes=$(wc -c < /tmp/cc.html) curl_captcha=$(grep -ci 'validateCaptcha' /tmp/cc.html)" >> "$LOG"
done
echo "done $(date -Is)" >> "$LOG"
