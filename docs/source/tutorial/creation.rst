Creation
========

Let's look at the list:

.. include:: http/monitors-empty.http
    :code:

It's empty. But we can try posting new objects:

.. include:: http/monitor-post-empty-body.http
    :code:

Let's provide the required fields and some additional information:

.. include:: http/monitor-post.http
    :code:

Success! And the object is seen on the list

.. include:: http/monitors-with-object.http
    :code:


