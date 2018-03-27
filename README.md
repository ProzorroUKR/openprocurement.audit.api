# openprocurement.audit.api

Installation
*  Clone
*  `python bootstrap.py`
*  `bin/buildout -N`

Then you can run test
*  `bin/nosetests`


Description

The State Audit Service of Ukraine (SAS / ДАСУ)
Державна аудиторська служба України (Держаудитслужба) є центральним органом виконавчої влади, дiяльнiсть якого спрямовується i координується Кабiнетом Мiнiстрiв України та який забезпечує формування i реалiзує державну полiтику у сферi державного фiнансового контролю.

The module provides ability to start and publish monitoring processes of open procurement tenders 
in order to prevent any violations of the law.

There are two types of users use the module: 
* SAS staff (they can manage monitoring objects)
* brokers (deliver tender owners' responses and clarifications regarding open monitoring objects)

`auth.ini`  should contain [sas] group so that SAS staff users are able to pass the authorization

