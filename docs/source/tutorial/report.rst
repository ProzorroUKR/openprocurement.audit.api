.. include:: defs.hrst

Violation Elimination Report
============================

.. tip::
    | This section contains available actions for next roles:
    | |no| Monitoring owner
    | |yes| Tender owner

As soon as the monitoring in ``addressed`` status, its tender owner can provide a report about violation eliminations:

.. include:: http/elimination-report-post.http
   :code:

We have already seen how to get ``acc_token`` in :ref:`credentials` section

Now let's update our report:

.. include:: http/elimination-report-edit.http
   :code:

That's it.
