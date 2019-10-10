.. include:: ../../images.hrst

Monitoring Documents
====================

.. note::
    | This section contains available actions for next roles:
    | |yes| Monitoring owner
    | |no| Tender owner

As soon as the monitoring goes to terminal status (``cancelled``,  ``stopped``, ``completed``, ``closed``), SAS-employee can add documents to monitoring

.. include:: http/monitoring-documents.http
   :code:


To update a document, you can use PUT method as follows

.. include:: http/monitoring-documents-put.http
   :code:


The initial version is shown in "previousVersions" field

.. include:: http/monitoring-documents-get.http
   :code:


It also possible to update the document info (but not the document itself). This method doesn't produce a new version

.. include:: http/monitoring-documents-patch.http
   :code:

The eventual list should will look like this

.. include:: http/monitoring-documents-get-collection.http
   :code:
