.. include:: defs.hrst

.. _dialogue:

Make a Dialogue
===============

.. note::
    | This section contains available actions for next roles:
    | |yes| Monitoring owner
    | |yes| Tender owner


For published monitoring we can start dialogue by publishing a post as a SAS-employee:

.. include:: http/post-publish.http
    :code:

Lets add another document to a post:

.. include:: http/post-publish-add-document.http
    :code:

We also can get a list of all post documents:

.. include:: http/post-get-documents.http
    :code:

To answer the question as a broker we must get :ref:`credentials` first. Now lets add an answer using generated token:

.. include:: http/post-answer.http
    :code:

And also add documents:

.. include:: http/post-answer-docs.http
    :code:

Also we can create another question as a broker by publishing an another post:

.. include:: http/post-broker-publish.http
    :code:

And also SAS-employee can publish an answer post:

.. include:: http/post-broker-sas-answer.http
    :code:

Lets see all posts we have:

.. include:: http/posts-get.http
    :code:
