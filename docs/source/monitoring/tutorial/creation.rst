.. include:: ../../images.hrst

Monitoring Creation
===================

.. note::
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

Success! Please note that monitoring is in 'draft' status. Monitorings in 'draft' status are not visible in general list. Such monitorings would only be visible in a separate feed (mode=real_draft) and you'll need an acess token to see them:

.. include:: http/monitorings-with-object.http
    :code:


