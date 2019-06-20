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


Documentation
----------------------

1. Install requirements by running::

    pip install -r requirements.txt -e .[test,docs]

2. Add "couchdb" to be resolved to localhost in /etc/hosts::

    echo "127.0.0.1 couchdb" >> /etc/hosts

3. To run couchdb if you don't have one::

    docker-compose up -d

Update documentation
--------------------
Running tests to update http files::

    py.test doc.py  # all

    py.test doc.py -k test_case  # specific

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

