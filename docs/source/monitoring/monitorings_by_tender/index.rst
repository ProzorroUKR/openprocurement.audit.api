.. include:: ../../images.hrst

Monitorings by tender id
========================

All the monitorings can be found by theirs tender id:

.. include:: http/monitorings-by-tender-id.http
    :code:

The ``opt_fields`` param is supported:

.. include:: http/monitorings-by-tender-id-opt-fields.http
    :code:

Pagination can be controlled with ``limit`` and ``page`` params where:

* ``limit`` - the maximum number of items
* ``page`` - the number of page

.. include:: http/monitorings-by-tender-id-pagination.http
    :code:
