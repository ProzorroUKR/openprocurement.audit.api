Publishing
==========

We are supposed to change the status of our monitor to publish it:

.. include:: http/monitor-publish-wo-decision.http
    :code:

Let's provide our publish party:

.. include:: http/monitor-publish-party.http
    :code:

Let's provide our decision:

.. include:: http/monitor-publish-first-step.http
    :code:

Also we can add documents one by one. Documents uploading should
follow the `upload <http://documentservice.api-docs.openprocurement.org>`_ rules.

.. include:: http/monitor-publish-add-document.http
    :code:

And finally activate tender:

.. include:: http/monitor-publish-second-step.http
    :code:

Success! Our monitor object has been published.

After monitor is published we can't change decision any more.

.. include:: http/monitor-publish-change.http
    :code:

Also we can publish decision with single request:

.. include:: http/monitor-publish.http
    :code:
