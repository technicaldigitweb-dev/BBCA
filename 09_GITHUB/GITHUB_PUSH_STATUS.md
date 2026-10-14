# GITHUB PUSH STATUS — BBOX

**Verified by command on 2026-10-14. No push status is claimed without a real commit hash.**

---

## Repository

| Field | Value |
|---|---|
| Remote | `origin` → `https://github.com/technicaldigitweb-dev/BBCA.git` |
| Branch | `main` |
| Upstream tracking | `origin/main` — configured |
| Repository root | `C:\Users\LED 222\Buy_Box_Check_Automation_Tharsi` |

## Commit on record

| Field | Value |
|---|---|
| Commit | `531cb38930427e92ca3f92eb7d8dd82fa1b977fd` |
| Short | `531cb38` |
| Message | `Initial BBCA project setup - Apirame` |
| Author | Apirame |
| Date | 2026-10-14 17:09:30 +0530 |
| Tracked files at that commit | 107 |
| Push state | `origin/main` resolved to the **same** commit — **pushed** |

## Changes made during this reorganisation — NOT yet committed

| Change | Files |
|---|---|
| New documentation folders populated | `00_PROJECT_CONTROL/` (4), `01_REQUIREMENT/` (3), `02_DISCOVERY/` (4), `07_AUTOMATION/` (1), `08_VALIDATION/` (3), `09_GITHUB/` (2), `10_HANDOVER/` (3), `11_DAILY_STATUS/` (1), `12_PROMPTS/` (1) |
| Asset register generator | `00_PROJECT_CONTROL/gen_asset_register.py` |
| **Security fix** | `automation/config.local.json` **untracked**; `automation/config.local.example.json` added; `.gitignore` extended |

**No source file was moved or rewritten.** The reorganisation is additive documentation
plus one repository-hygiene fix.

## Security fix detail

`automation/config.local.json` was committed in `531cb38` carrying:

```json
{ "gates": { "publish_approved": true }, "publish_audience": [ ... ] }
```

It holds no password, so this is not a credential leak. But it is an **operator-local
override**, and committing it means anyone cloning the repository inherits an **open
publish gate** — a clone could publish to `ph_task` without the operator intending it.
`automation/README.md` already stated the file is "not version controlled"; the commit
contradicted that.

Fixed: removed from the index (kept on disk), added to `.gitignore`, and a sanitised
`config.local.example.json` committed in its place.

## Files excluded from Git

From `.gitignore`: `__pycache__/`, `*.pyc`, `.venv/`, `.env*`, `*.db` / `*.sqlite*`,
`*.log`, `automation/state/`, `*.pem`, `*.key`, `*credentials*.json`, `*secrets*.json`,
`*token*.json`, and now `automation/config.local.json`.

Verified excluded: the SQLite history (`automation/state/buy_box_history.db`), run logs,
and the run lock.

## Commit plan for this reorganisation

```bash
git add 00_PROJECT_CONTROL 01_REQUIREMENT 02_DISCOVERY 07_AUTOMATION \
        08_VALIDATION 09_GITHUB 10_HANDOVER 11_DAILY_STATUS 12_PROMPTS \
        .gitignore automation/config.local.example.json
git rm --cached automation/config.local.json      # already staged
git commit -m "Mini-AIOS structure, evidence registers and repo hygiene - Apirame"
git push origin main
```

## Blockers

| Item | State |
|---|---|
| Remote configured | **resolved** |
| Authorisation to push | assumed — the account already pushed `531cb38` successfully |
| Large files | three dashboards total 8.5 MB; `04_DATA` is 83 MB. **Confirm whether `04_DATA` belongs in Git** — it is currently tracked and will grow each run |

## Honest statement

The initial commit exists and was pushed. **The reorganisation changes above are written
to disk but not committed or pushed at the time of writing.** No commit hash is claimed
for them. The `git add`/`commit`/`push` above has not been executed, because commits and
pushes are the operator's call under the Mini-AIOS operating rule.
