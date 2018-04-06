Creation of a monitoring object
===============================

Let's look at the list:

.. include:: http/empty-listing.http
    :code:

It's empty. But we can try posting new objects:

.. include:: http/post-monitor-empty-body.http
    :code:

Let's provide the required fields:

.. include:: http/post-monitor.http
    :code:

Success! And the object is seen on the list

.. include:: http/listing-with-object.http
    :code:


