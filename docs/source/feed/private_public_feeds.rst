.. _private_public_feeds:

Public vs Private feeds
=======================


.. _public_feeds:

Public feeds
------------

Changes or DateModified feeds may not display monitoring objects in some cases (`draft` status, `cancelled` status, ...)
If we have `draft`, `cancelled` and `active` monitoring objects, only the last one is shown on the public lists:

Changes

.. include:: http/public-changes-feed.http
    :code:

Date Modified

.. include:: http/public-date-modified-feed.http
    :code:

Monitoring by tender

.. include:: http/public-tender-monitorings.http
    :code:


And this is also true for TEST mode:

Changes [test]

.. include:: http/public-test-changes-feed.http
    :code:

Date Modified [test]

.. include:: http/public-test-date-modified-feed.http
    :code:

Monitoring by tender [test]

.. include:: http/public-test-tender-monitorings.http
    :code:


.. _private_feeds:

Private feeds
-------------

Private feeds show `draft` and `cancelled` objects:

But private feeds can be accessed as long as the right authorisation is provided

.. include:: http/private-changes-feed-forbidden.http
    :code:

Changes

.. include:: http/private-changes-feed.http
    :code:

Date Modified

.. include:: http/private-date-modified-feed.http
    :code:

Monitoring by tender

.. include:: http/private-tender-monitorings.http
    :code:


Private feeds for TEST mode:

Changes [test]

.. include:: http/private-test-changes-feed.http
    :code:

Date Modified [test]

.. include:: http/private-test-date-modified-feed.http
    :code:

Monitoring by tender [test] feed is not implemented.


