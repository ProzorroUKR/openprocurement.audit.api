.. include:: defs.hrst

Decision Publishing
===================

.. note::
    | This section contains available actions for next roles:
    | |yes| Monitoring owner
    | |no| Tender owner

We are supposed to change the status of our monitoring to publish it:

.. include:: http/monitoring-publish-wo-decision.http
    :code:

Let's provide our publish party:

.. include:: http/monitoring-publish-party.http
    :code:

Let's provide our decision:

.. include:: http/monitoring-publish-first-step.http
    :code:

Also we can add documents one by one. Documents uploading should
follow the `upload <http://documentservice.api-docs.openprocurement.org>`_ rules.

.. include:: http/monitoring-publish-add-document.http
    :code:

And finally activate tender:

.. include:: http/monitoring-publish-second-step.http
    :code:

Success! Our monitoring object has been published.

After monitoring is published we can't change decision any more.

.. include:: http/monitoring-publish-change.http
    :code:

Also we can publish decision with single request:

.. include:: http/monitoring-publish.http
    :code:
