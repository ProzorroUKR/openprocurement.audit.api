Configuration
==============


restricted
------------
Tenders have configuration that indicates whether the tender has restricted access.
This configuration relates to monitoring too.

During monitoring creation configuration `restricted` is moving from tender.

Let's create monitoring for tender with `restricted: True` value:

.. include:: http/post-monitoring-restricted-true.http
    :code:

After adding some kind of monitoring objects some fields will be masked depends on `restricted` configuration.

List of monitoring masked fields:

.. csv-table::
   :file: csv/monitoring-mask-mapping.csv
   :header-rows: 1

Let's look at monitoring with role SAS:

.. include:: http/get-monitoring-restricted-true-sas.http
    :code:

Let's look at monitoring with role `broker`:

.. include:: http/get-monitoring-restricted-true-brokerr.http
    :code:

Let's look at monitoring as unauthorized user or as broker who doesn't have accreditation to see restricted fields:

.. include:: http/get-monitoring-restricted-true-broker.http
    :code: