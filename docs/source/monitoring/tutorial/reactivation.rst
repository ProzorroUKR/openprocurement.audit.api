.. include:: ../../images.hrst

Reactivation Monitoring
========================

.. note::
    | This section contains available actions for next roles:
    | |yes| Monitoring owner
    | |no| Tender owner


If monitoring has ``stopped`` status, SAS-employee can activate one more time monitoring with ``active`` status.
During that process new ``monitoringPeriod.endDate`` will be calculated, if monitoring has stopped in this period and some working days are left.

Let's look at monitoring, that was ``stopped`` at 5th working day:

.. include:: http/stopped-monitoring.http
   :code:

Let's activate one more time monitoring in 6 days (``2025-11-11T10:00:00+02:00``).
10 working days of period are left during stopping, that's why new ``monitoringPeriod.endDate`` will be calculated:

.. include:: http/stopped-monitoring-to-active.http
   :code:

There is a possibility reactivate ``stopped`` monitoring and stop ``active`` monitoring only once.
If we try to stop one more time this monitoring we will see an error:

.. include:: http/active-monitoring-to-stopped-second-time.http
   :code:
