.. include:: defs.hrst

.. _dialogue:

Make a Dialogue
===============

.. note::
    | This section contains available actions for next roles:
    | |yes| Monitoring owner
    | |yes| Tender owner


Let's provide party that will be used as related party for our dialogue:

.. include:: http/dialogue-party.http
    :code:

For published monitoring we can start dialogue:

.. include:: http/dialogue-publish.http
    :code:

Lets add another document to dialogue:

.. include:: http/dialogue-publish-add-document.http
    :code:

We also can get a list of all dialogue documents:

.. include:: http/dialogue-get-documents.http
    :code:

To answer the question as a broker we must get :ref:`credentials` first. Now lets update answer using generated token:

.. include:: http/dialogue-answer.http
    :code:

And also add documents:

.. include:: http/dialogue-answer-docs.http
    :code:

Lets see the result dialogue:

.. include:: http/dialogue-get.http
    :code:

Also we can create another question as a broker:

.. include:: http/dialogue-broker-publish.http
    :code:

Lets see all dialogues we have:

.. include:: http/dialogue-get.http
    :code:
