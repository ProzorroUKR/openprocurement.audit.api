.. include:: ../../images.hrst

Tutorial
========

Here is the list of inspections:

.. include:: http/inspection-list-empty.http
    :code:

There are no inspections, so let's post one:

.. include:: http/inspection-post.http
    :code:


Documents can be added to the object:

.. include:: http/inspection-document-post.http
    :code:

Documents can be changed:

.. include:: http/inspection-document-put.http
    :code:


And the object itself can be changed:

.. include:: http/inspection-patch.http
    :code:
