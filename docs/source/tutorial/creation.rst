.. include:: defs.hrst

Monitoring Creation
===================

.. tip::
    | This section contains available actions for next roles:
    | |yes| Monitoring owner
    | |no| Tender owner

Let's look at the list:

.. include:: http/monitorings-empty.http
    :code:

It's empty. But we can try posting new objects:

.. include:: http/monitoring-post-empty-body.http
    :code:

Let's provide the required fields and some additional information:

.. include:: http/monitoring-post.http
    :code:

Success! And the object is seen on the list

.. include:: http/monitorings-with-object.http
    :code:


