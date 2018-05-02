.. image:: https://travis-ci.org/raccoongang/openprocurement.audit.api.svg
    :target: https://travis-ci.org/raccoongang/openprocurement.audit.api


.. image:: https://img.shields.io/hexpm/l/plug.svg
    :target: https://github.com/raccoongang/openprocurement.audit.api/blob/master/LICENSE.txt


.. image:: https://coveralls.io/repos/github/raccoongang/openprocurement.audit.api/badge.svg
    :target: https://coveralls.io/github/raccoongang/openprocurement.audit.api


.. image:: https://readthedocs.org/projects/sas-api-raccoongang-my/badge/?version=latest
    :target: http://sas-api-raccoongang-my.readthedocs.io/en/latest/?badge=latest
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

