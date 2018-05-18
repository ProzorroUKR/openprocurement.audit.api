.. _dialogue:

Make a Dialogue
===============

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

To answer the question as a broker we must get credentials first.

In order to get rights for future monitoring editing, we need to use this view ``PATCH: /monitorings/{id}/credentials?acc_token={tender_token}`` with the API key of the eMall (broker), where tender was generated.

In the ``PATCH: /contracts/{id}/credentials?acc_token={tender_token}``:

* ``id`` stands for monitoring id,

* ``tender_token`` is tender's token (is used for monitoring token generation).

Response will contain ``access.token`` for the contract that can be used for further monitoring modification.

.. include:: http/dialogue-get-credentials.http
    :code:

Now lets update answer using generated token:

.. include:: http/dialogue-answer.http
    :code:

And also add documents:

.. include:: http/dialogue-answer-docs.http
    :code:

Lets see the result dialogue:

.. include:: http/dialogue-get.http
    :code:
