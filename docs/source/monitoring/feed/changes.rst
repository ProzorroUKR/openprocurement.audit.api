Changes feed
============

Changes feed is the best option for synchronization with the SAS monitoring database.
Let's use :code:`feed=changes` to get monitors sorted by changes ascending:

.. include:: http/changes-feed.http
    :code:

The response contains :code:`next_page`. Every time we use it, we get monitors with changes that haven't been synced yet.

.. include:: http/changes-feed-next.http
    :code:

Let's proceed to the last page:

.. include:: http/changes-feed-last.http
    :code:

Since there are no results, let's wait before we try it again:

.. include:: http/changes-feed-new.http
    :code:

And the next page can either be empty again

.. include:: http/changes-feed-new-next.http
    :code:


or contain a monitor with new changes

.. include:: http/changes-feed-new-last.http
    :code: