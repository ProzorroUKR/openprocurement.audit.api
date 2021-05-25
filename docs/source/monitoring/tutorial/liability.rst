.. include:: ../../images.hrst

Liability
=========

.. note::
    | This section contains available actions for next roles:
    | |yes| Monitoring owner
    | |no| Tender owner


After publication the elimination resolution (monitoring in status `addressed`), monitoring owner can add liability:

.. include:: http/liability-post.http
   :code:


After adding the liability(monitoring in status: `addressed` or `complete`), to liability can be added proceeding:

.. include:: http/add-proceeding-to-liability.http
   :code:

This action also can be performed only once:

.. include:: http/add-proceeding-to-liability-again.http
   :code:


Documents can be added/changed/replaced any time:

.. include:: http/liability-post-doc.http
   :code:

.. include:: http/liability-patch-doc.http
   :code:

.. include:: http/liability-put-doc.http
   :code:
