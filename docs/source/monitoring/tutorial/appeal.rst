.. include:: ../../images.hrst

Appeal
======

.. note::
    | This section contains available actions for next roles:
    | |no| Monitoring owner
    | |yes| Tender owner


We have already seen how to get ``acc_token`` in :ref:`credentials` section

As soon as the conclusion is published, tender's owner may point out that the conclusion has been appealed in court:

.. include:: http/appeal-post.http
   :code:


This action can be performed only once:

.. include:: http/appeal-post-again.http
   :code:

Documents can be added/changed any time:

.. include:: http/appeal-post-doc.http
   :code:

.. include:: http/appeal-patch-doc.http
   :code:
