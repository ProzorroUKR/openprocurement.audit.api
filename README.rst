OpenProcurement Audit Api
=========================


Installation
------------
Run::

    docker-compose build

    docker-compose up


Description
-----------

The State Audit Service of Ukraine (SAS / ДАСУ)
Державна аудиторська служба України (Держаудитслужба) є центральним органом виконавчої влади, дiяльнiсть якого спрямовується i координується Кабiнетом Мiнiстрiв України та який забезпечує формування i реалiзує державну полiтику у сферi державного фiнансового контролю.

The module provides ability to start and publish monitoring processes of open procurement tenders
in order to prevent any violations of the law.

There are two types of users use the module:
- SAS staff (they can manage monitoring objects)
- brokers (deliver tender owners' responses and clarifications regarding open monitoring objects)

`auth.ini`  should contain [sas] group so that SAS staff users are able to pass the authorization


Security scan
-------------

Three checks run in the ``lint`` stage of the pipeline next to ruff and mypy:

- **Bandit** scans our own Python code and blocks the pipeline from day one.
- **osv-scanner** checks ``uv.lock`` against the OSV vulnerability database.
- **gitleaks** checks the diff of every new commit for secrets.

osv-scanner and gitleaks start in observation mode (the job may fail, the pipeline stays green).
They switch to blocking mode when ``OSV_BLOCKING`` / ``GITLEAKS_BLOCKING`` are set to ``"true"``
in the project CI/CD variables; no code change is needed.

Run the same checks locally before opening a merge request or when a job goes red::

    uv run bandit -r openprocurement/ -c pyproject.toml   # own code
    make audit                             # dependencies (or ./osv_scan.sh)
    gitleaks git . --redact                # secrets in commits (gitleaks dir . for the working tree)

``make audit`` runs the scanner from a pinned Docker image (or a local ``osv-scanner`` binary if
present) so a local run and the CI job give the same result. The vulnerability database is
downloaded into the ``osv-db`` docker volume and the comparison happens locally: package names
are never sent anywhere. Other formats: ``make audit OSV_FORMAT=table`` / ``html`` / ``json``.

Known vulnerabilities that we cannot or should not fix are listed in ``osv-scanner.toml``;
every entry has a ``reason`` and an ``ignoreUntil`` date, after which the finding comes back.
Bandit exceptions are ``# nosec BXXX`` comments with a reason on the line; the ``[tool.bandit]``
section of ``pyproject.toml`` only excludes test and migration directories. gitleaks exceptions
live in ``.gitleaks.toml`` and cover only ``generic-api-key`` for test tokens under ``docs/``,
``tests/`` and ``etc/``.

Dependencies installed from git (``[tool.uv.sources]`` in ``pyproject.toml``) have no version
the scanner can match, so they are reviewed by hand whenever a revision in ``[tool.uv.sources]`` changes.

Documentation
----------------------

1. Install requirements by running::

    uv sync

2. Add "couchdb" to be resolved to localhost in /etc/hosts::

    echo "127.0.0.1 couchdb" >> /etc/hosts

3. To run couchdb if you don't have one::

    docker-compose up -d

Update documentation
--------------------
Running tests to update http files::

    py.test docs.py  # all

    py.test docs.py -k test_case  # specific

Build documentation
-------------------

Run::

    cd docs

    make html

Translation
-----------

For translation into *uk* (2 letter ISO language code), you have to follow the scenario:

1. Pull all translatable strings out of documentation::

    cd docs

    make gettext

2. Update translation with new/changed strings::

    cd docs

    sphinx-intl update -p build/locale -l uk

3. Update updated/missing strings in `docs/source/locale/<lang>/LC_MESSAGES/*.po` with your-favorite-editor/poedit/transifex/pootle/etc. to have all translations complete/updated.

4. Compile the translation::

    cd docs

    sphinx-intl build

