.. include:: ../../images.hrst

Tutorial
========

Here is the list of inspections:

.. include:: http/inspection-list-empty.http
    :code:

There are no inspections, so let's post one:

.. include:: http/inspection-post.http
    :code:


Documents can be added to the object:

.. include:: http/inspection-document-post.http
    :code:

Documents can be changed:

.. include:: http/inspection-document-put.http
    :code:


And the object itself can be changed:

.. include:: http/inspection-patch.http
    :code:


Configuration
==============


restricted
------------
Tenders have configuration that indicates whether the tender has restricted access.
This configuration relates to monitoring too.

During monitoring creation configuration `restricted` is moving from tender.

During inspection creation, if there are at least one monitoring in `monitoring_ids` with `restricted: True` value,
this configuration is moving to inspection as `restricted: True`. In others cases `restricted` will have value `False`.

Let's create inspection for monitoring with `restricted: True` value:

.. include:: http/post-inspection-restricted-true.http
    :code:

Some fields will be masked depends on `restricted` configuration.

List of inspection masked fields:

.. csv-table::
   :file: csv/inspection-mask-mapping.csv
   :header-rows: 1

Let's look at inspection with role SAS:

.. include:: http/get-inspection-restricted-true-sas.http
    :code:

Let's look at inspection with role `broker`:

.. include:: http/get-inspection-restricted-true-brokerr.http
    :code:

Let's look at inspection as unauthorized user or as broker who doesn't have accreditation to see restricted fields:

.. include:: http/get-inspection-restricted-true-broker.http
    :code: