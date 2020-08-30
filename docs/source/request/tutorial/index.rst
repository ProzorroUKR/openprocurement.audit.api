.. include:: ../../images.hrst

Tutorial
========

Here is the list of requests:

.. include:: http/request-list-empty.http
    :code:

There are no requests, so let's post one:

.. note::
    Next action allowed to users that belongs to next auth group:
    ``public``

.. include:: http/request-post.http
    :code:

Documents can be added to the object with separate request:

.. note::
    Next action allowed to users that belongs to next auth group:
    ``public``

.. include:: http/request-document-post.http
    :code:

Documents can be changed:

.. note::
    Next action allowed to users that belongs to next auth group:
    ``public``

.. include:: http/request-document-put.http
    :code:


And the object itself can be changed by patching `answer` field only:


.. note::
    Next action allowed to users that belongs to next auth group:
    ``sas``

.. include:: http/request-patch.http
    :code:

Lets take a look at request. Notice that `address` field is not visible in public api:

.. include:: http/request-get-no-auth.http
    :code:

But `address` field would be visible for reviewer and you'll need an access token to see it:


.. note::
    Next action allowed to users that belongs to next auth group:
    ``sas``

.. include:: http/request-get-sas.http
    :code:
