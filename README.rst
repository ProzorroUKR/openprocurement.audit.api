.. image:: https://travis-ci.org/ProzorroUKR/openprocurement.audit.api.svg
    :target: https://travis-ci.org/ProzorroUKR/openprocurement.audit.api


.. image:: https://img.shields.io/hexpm/l/plug.svg
    :target: https://github.com/ProzorroUKR/openprocurement.audit.api/blob/master/LICENSE.txt


.. image:: https://coveralls.io/repos/github/ProzorroUKR/openprocurement.audit.api/badge.svg
    :target: https://coveralls.io/github/ProzorroUKR/openprocurement.audit.api


.. image:: https://readthedocs.org/projects/prozorro-audit-api/badge/?version=latest
    :target: http://prozorro-audit-api.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status



Installation
------------
-  Clone
-  `./bootstrap.sh`
-  `bin/buildout -N`

Then you can run test
-  `bin/nosetests`


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


Building documentation
----------------------

Use following commands to build documentation from `docs/source` into `docs/html`::

 bin/buildout -N -c docs.cfg
 bin/docs

For translation into *<lang>* (2 letter ISO language code), you have to follow the scenario:

 1. Pull all translatable strings out of documentation::

     (cd docs/build; make gettext)

 2. Update translation with new/changed strings::

     bin/sphinx-intl update -c docs/source/conf.py -p docs/build/locale -l uk

 3. Update updated/missing strings in `docs/source/locale/<lang>/LC_MESSAGES/*.po` with your-favorite-editor/poedit/transifex/pootle/etc. to have all translations complete/updated.

 4. Compile the translation::

      bin/sphinx-intl build -c docs/source/conf.py

 5. Build translated documentations::

     (cd docs/build; make -e SPHINXOPTS="-D language='uk'" html)

