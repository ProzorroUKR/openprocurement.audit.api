Conclusion
==========


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


Also we can add documents one by one. Documents uploading should
follow the `upload <http://documentservice.api-docs.openprocurement.org>`_ rules.

.. include:: http/conclusion-add-document.http
   :code:

