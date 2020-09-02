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

Documents related to answer also can be added to the object with separate request:

.. note::
    Next action allowed to users that belongs to next auth group:
    ``sas``

.. include:: http/request-document-sas-post.http
    :code:

Lets get all request documents:

.. include:: http/request-documents-get.http
    :code:

Once answer has been provided it can no longer be changed, lets make an attempt:

.. note::
    Next action allowed to users that belongs to next auth group:
    ``sas``

.. include:: http/request-patch-forbidden.http
    :code:

Lets take a look at request. Notice that part of `parties` fields is not visible in public api:

.. include:: http/request-get-no-auth.http
    :code:

But hidden `parties` fields would be visible for reviewer and you'll need an access token to see it:

.. note::
    Next action allowed to users that belongs to next auth group:
    ``sas``

.. include:: http/request-get-sas.http
    :code:

Lets add another request and leave it without an answer:

.. include:: http/request-post-not-answered.http
    :code:

Here are all available requests:

.. include:: http/requests-list.http
    :code:

Feed modes available:

* by default - all real requests
* ``mode=real_answered`` - real requests that have an answer
* ``mode=real_not_answered`` - real requests that dont't have an answer
* ``mode=test`` - all test requests
* ``mode=test_answered`` - test requests that have an answer
* ``mode=test_not_answered`` - test requests that dont't have an answer

For example:

.. include:: http/requests-list-answered.http
    :code:
