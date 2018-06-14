.. include:: defs.hrst

Conclusion Publishing
=====================

.. note::
    | This section contains available actions for next roles:
    | |yes| Monitoring owner
    | |no| Tender owner


Conclusion object contains results about any violations have been found during monitoring.
In case there are no violations, the conclusion may be filled the following way:

.. include:: http/conclusion-wo-violations.http
   :code:

Otherwise we are expected to provide more details:

.. include:: http/conclusion-failed-required.http
   :code:


Let's provide all the possible fields:

.. include::  http/conclusion-full.http
   :code:

If you want add a violation that is not on the list, you can add `other` to the list.
In this case you are supposed to provide details of the violation:

.. include::  http/conclusion-other-validation.http
   :code:


Also we can add documents one by one. Documents uploading should
follow the `upload <http://documentservice.api-docs.openprocurement.org>`_ rules.

.. include:: http/conclusion-add-document.http
   :code:

To finalize conclusion process status must be changed to ``addressed`` in case of violations occurred or to ``declined`` otherwise:

.. include:: http/conclusion-addressed.http
   :code:

Broker can initiate dialogue once after conclusion was provided:

.. include:: http/conclusion-dialogue.http
   :code:

In case of no violations occurred SAS-employer can close monitoring by changing status to ``closed``:

.. include:: http/monitoring-to-closed.http
   :code:
