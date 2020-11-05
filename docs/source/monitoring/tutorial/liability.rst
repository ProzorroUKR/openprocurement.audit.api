.. include:: ../../images.hrst

Liability
=========

.. note::
    | This section contains available actions for next roles:
    | |yes| Monitoring owner
    | |no| Tender owner


As soon as the elimination resolution is published, monitoring owner can add liability:

.. include:: http/liability-post.http
   :code:


This action can be performed only once:

.. include:: http/liability-post-again.http
   :code:

After adding the liability, to liability can be added proceeding:

.. include:: http/add-proceeding-to-liability.http
   :code:

This action also can be performed only once:

.. include:: http/add-proceeding-to-liability-again.http
   :code:


Documents can be added/changed any time:

.. include:: http/liability-post-doc.http
   :code:

.. include:: http/liability-patch-doc.http
   :code:
