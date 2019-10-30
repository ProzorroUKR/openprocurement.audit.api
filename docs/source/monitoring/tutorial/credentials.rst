.. include:: ../../images.hrst

.. _credentials:

Credentials
===========

.. note::
    | This section contains available actions for next roles:
    | |no| Monitoring owner
    | |yes| Tender owner

In order to get rights for future monitoring editing as a broker, we need to use this view ``PATCH: /monitorings/{id}/credentials`` with the API key of the eMall (broker), where tender was generated.

You can pass access token in the following ways:

1) ``acc_token`` URL query string parameter
2) ``X-Access-Token`` HTTP request header
3) ``access.token`` in the body of request

In the ``PATCH: /monitorings/{id}/credentials?acc_token={tender_token}``:

* ``id`` stands for monitoring id,

* ``tender_token`` is tender's token (is used for monitoring token generation).

Response will contain ``access.token`` for the contract that can be used for further monitoring modification.

.. include:: http/dialogue-get-credentials.http
    :code:
