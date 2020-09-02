.. include:: ../../images.hrst

Inspections by monitoring id
============================

All the inspections can be found by theirs monitoring id:

.. include:: http/inspections-by-monitoring_id.http
    :code:

The ``opt_fields`` param is supported:

.. include:: http/inspections-by-monitoring_id-opt_fields.http
    :code:

Pagination can be controlled with ``limit`` and ``page`` params where:
    * ``limit`` - the maximum number of items
    * ``page`` - the number of page

.. include:: http/inspections-by-monitoring_id-pagination.http
    :code:
