|Tag| |License|

.. raw:: html

  <div align="center">
    <h1><code>amlight/sdntrace_cp</code></h1>

    <strong> Napp that traces OpenFlow paths in the control plane</strong>

    <h3><a href="https://kytos-ng.github.io/api/sdntrace_cp.html">OpenAPI Docs</a></h3>
  </div>


Overview
========
Run tracepaths on OpenFlow in the Control Plane

Installing
==========

To install this NApp, first, make sure to have the same venv activated as you have ``kytos`` installed on:

.. code:: shell

   $ git clone https://github.com/amlight/sdntrace_cp.git
   $ cd sdntrace_cp
   $ python setup.py develop

Requirements
============

- `amlight/flow_stats <https://github.com/amlight/flow_stats>`_
- `amlight/scheduler <https://github.com/amlight/scheduler>`_


Events
======

Subscribed
----------

- ``amlight/flow_stats.flows_updated``


.. TAGs

.. |License| image:: https://img.shields.io/github/license/amlight/sdntrace_cp.svg
   :target: https://github.com/amlight/sdntrace_cp/blob/master/LICENSE
.. |Build| image:: https://scrutinizer-ci.com/g/amlight/sdntrace_cp/badges/build.png?b=master
  :alt: Build status
  :target: https://scrutinizer-ci.com/g/amlight/sdntrace_cp/?branch=master
.. |Coverage| image:: https://scrutinizer-ci.com/g/amlight/sdntrace_cp/badges/coverage.png?b=master
  :alt: Code coverage
  :target: https://scrutinizer-ci.com/g/amlight/sdntrace_cp/?branch=master
.. |Quality| image:: https://scrutinizer-ci.com/g/amlight/sdntrace_cp/badges/quality-score.png?b=master
  :alt: Code-quality score
  :target: https://scrutinizer-ci.com/g/amlight/sdntrace_cp/?branch=master
.. |Stable| image:: https://img.shields.io/badge/stability-stable-green.svg
   :target: https://github.com/amlight/sdntrace_cp
.. |Tag| image:: https://img.shields.io/github/tag/amlight/sdntrace_cp.svg
   :target: https://github.com/amlight/sdntrace_cp/tags
