.. include:: ../../images.hrst

Appeal
======

.. note::
    | This section contains available actions for next roles:
    | |no| Monitoring owner
    | |yes| Tender owner


We have already seen how to get ``acc_token`` in :ref:`credentials` section

After publication conclusion by SAS (monitoring in status `addressed` or `declined` ),
the tender owner may point out that the conclusion has been appealed in court.
In this case the object of legislation is automatically filled by CDB:

.. include:: http/appeal-post.http
   :code:


This action can be performed only once:

.. include:: http/appeal-post-again.http
   :code:

After adding the appeal (monitoring in status: `addressed`/`complete`/`declined`/`closed`/`stopped`), to appeal can be added proceeding:

.. include:: http/add-proceeding-to-appeal.http
   :code:

This action also can be performed only once:

.. include:: http/add-proceeding-to-appeal-again.http
   :code:


Documents can be added/changed/replaced any time:

.. include:: http/appeal-post-doc.http
   :code:

.. include:: http/appeal-patch-doc.http
   :code:

.. include:: http/appeal-put-doc.http
   :code:
