# Security flow

Репозиторій: `cdb/openprocurement.audit.api`. Еталонна реалізація: `openprocurement.api`.
Цей файл є записом підключення security flow: відповіді на питання до репозиторію, результати
першого запуску кожного сканера, список залежностей, яких сканер не бачить, і прийняті винятки.

## Пʼять питань до репозиторію

| Питання | Відповідь |
| --- | --- |
| Як оголошені залежності | `pyproject.toml` + `uv.lock` (uv). Сканер читає `uv.lock` напряму. Додатково `docs/source/requirements.txt` (4 пакети Sphinx, два без точної версії, сканер їх пропускає; у прод-образ не потрапляють). |
| Звідки береться CI | Власний `.gitlab-ci.yml` у репозиторії, стадія `lint` (аналог `check`). Джоби додано поруч із `ruff` і `mypy`. |
| Прод-образ і межа prod/dev | `Dockerfile`, `uv sync --frozen ${UV_EXTRA_ARGS}`. Для `master` і тегів `UV_EXTRA_ARGS="--no-dev"`, тому в прод-образ потрапляють лише `[project].dependencies`. Dev-група (`[dependency-groups].dev`): pytest, pytest-xdist, webtest, freezegun, python-coveralls, coverage, pytest-cov, parameterized, ruff, mypy, pre-commit, bandit. Образ для гілок збирається з dev-групою, але в прод не йде. |
| Чи є Bandit | Не було. Додано `bandit[toml]==1.7.7` у dev-групу, секцію `[tool.bandit]` у `pyproject.toml` і джоб `bandit`. |
| Чи репозиторій публічний | Є публічне дзеркало на GitHub (`ProzorroUKR/openprocurement.audit.api`, вказане як Homepage у `pyproject.toml`). Історію не переписуємо. |

## Bandit

- `[tool.bandit]`: `exclude_dirs = ["**/tests/**", "**/migrations/**", ".venv", "docs"]`, `skips = []`.
- Перший запуск (2026-10-10): 3 знахідки, усі закриті точковими `# nosec` з поясненням у коді:
  - `openprocurement/audit/api/rfc6266.py` B101 ×2: assert перевіряє внутрішні інваріанти
    (`build_header` викликається лише з `disposition="attachment"` і `filename_compat=quote(title)`), образ не запускається з `-O`.
  - `openprocurement/audit/api/utils.py` B413: `from Crypto.Cipher import AES` походить із pycryptodome, а не pycrypto; хибне спрацювання.
    Зауваження: функції `encrypt`/`decrypt` у цьому модулі не мають викликів у коді; кандидат на видалення окремою задачею.
- Локально: `uv run bandit -r . -c pyproject.toml` → `No issues identified`.

## osv-scanner

- Перший запуск (2026-10-10, osv-scanner 2.6.0): 107 пакетів в `uv.lock`, 7 із вразливостями, 17 унікальних вразливостей
  (0 Critical, 8 High, 9 Medium, 0 Low).
- Закрито оновленнями (тести зелені в обох режимах, `SANDBOX_MODE` порожній і `=1`):

  | Пакет | Було | Стало | Прод/dev | Вразливості |
  | --- | --- | --- | --- | --- |
  | pymongo | 4.17.0 | 4.18.3 | прод | GHSA-8fvv-fgr5-f8ch, GHSA-qx36-8mw2-4r3x, GHSA-v4x9-3549-crwv, GHSA-vp6j-j7w5-5xjj |
  | PyNaCl | 1.5.0 | 1.6.2 | прод | PYSEC-2026-3002 |
  | WebOb | 1.8.9 | 1.8.11 | прод | PYSEC-2026-251, PYSEC-2026-3943 |
  | urllib3 (транзитивна) | 2.7.0 | 2.8.0 | прод | PYSEC-2026-4175, PYSEC-2026-4176, PYSEC-2026-4177 |
  | setuptools | 78.1.0 | 81.0.0 | прод | PYSEC-2025-49 |
  | pytest | 8.3.5 | 9.0.3 | dev | PYSEC-2026-1845 |
  | virtualenv (транзитивна, через pre-commit) | 21.7.5 | 21.14.6 | dev | PYSEC-2026-4011, -4012, -4013, -4014 |

- Виняток у `osv-scanner.toml`: `PYSEC-2026-3447` (setuptools, CVE-2026-59890, CVSS 6.1), до 2027-03-21.
  Не застосовується (sdist не збираємо) і не можемо оновитись (фікс у 83.0.0, а 82.0.0 прибрав `pkg_resources`,
  який імпортують `app.py`, Pyramid і Cornice). Власника і ревʼюера треба заповнити.
- Після цього `make audit` → `No issues found`.

### Залежності з git, сканер їх не бачить

Перевіряти руками при кожній зміні ревізії: чи є advisory на osv.dev і чи не відстав форк від upstream.

| Пакет | Джерело | Ревізія |
| --- | --- | --- |
| schematics | ProzorroUKR/schematics | 1.1.3-prozorro.1 |
| openprocurement_client | ProzorroUKR/openprocurement.client.python | 2.2.0+dp |
| request_id_middleware | ProzorroUKR/request_id_middleware | 0.1.2 |
| openprocurement.subscribers.serverid | ProzorroUKR/openprocurement.subscribers.serverid | 2.0 |
| esculator | ProzorroUKR/esculator | 0.0.2 |
| dateorro | ProzorroUKR/dateorro | 0.0.3 |
| jsonpatch | ProzorroUKR/python-json-patch | 1.14+jsondiff.unicode.replacefix.0 |
| barbecue | ProzorroUKR/barbecue | 0.2 |
| standards | ProzorroUKR/standards | 1.0.110 |

## gitleaks

- Сканування всієї історії (410 комітів, gitleaks 8.30.1, `--redact`) без винятків: 258 знахідок, усі за правилом `generic-api-key`.
- Розбір: усі 258 є тестовими даними. 252 у `docs/source/**/http/*.http` (токени `acc_token`, `tender_owner_token`,
  `"token": "<hex>"`, які генерує `docs.py`), 4 у `openprocurement/audit/*/tests/tests.ini` (`dockey`),
  2 в `etc/service.ini` (`dockey`, `dockeys`). Ключ `dockey` є тим самим спільним тестовим ключем DS, що в тестових
  конфігах `openprocurement.api`. Мертвих і живих витоків не знайдено.
- `.gitleaks.toml`: виняток лише для `generic-api-key` за шляхами `docs/`, `tests/`, `etc/`
  з регулярними виразами під назви токенів цього репозиторію.
- Перевірка з файлом винятків: уся історія → 0, останні 50 комітів (`-m`) → 0, робоче дерево (`gitleaks dir .`) → 0.

## Завершення

- README: розділ «Security scan» з локальними командами.
- Дата підключення: 2026-10-10. Період спостереження: до 2026-10-31.
- Перехід у режим блокування: встановити `OSV_BLOCKING="true"` і `GITLEAKS_BLOCKING="true"`
  в Settings → CI/CD → Variables проєкту. Дата переходу: <не задана>.
- Реєстр винятків, рядки для внесення:

| Репозиторій | Інструмент | Знахідка | Причина, коротко | Власник | Погодив | Перегляд до | Стан |
| --- | --- | --- | --- | --- | --- | --- | --- |
| openprocurement.audit.api | osv-scanner | PYSEC-2026-3447, setuptools | Фікс прибирає pkg_resources, який імпортують app.py і Pyramid; sdist не збираємо | <команда> | <хто> | 21.03.2027 | активний |
| openprocurement.audit.api | Bandit | B101, rfc6266.py ×2 | Внутрішні інваріанти, образ не запускається з -O | <команда> | <хто> | <дата> | активний |
| openprocurement.audit.api | Bandit | B413, utils.py | pycryptodome, не pycrypto; хибне спрацювання | <команда> | <хто> | <дата> | активний |
| openprocurement.audit.api | gitleaks | generic-api-key у docs/, tests/, etc/ | Тестові токени sandbox і тестовий ключ DS | <команда> | <хто> | 10.10.2027 | активний |
