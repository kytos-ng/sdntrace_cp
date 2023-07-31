|Tag| |License| |Build| |Coverage| |Quality| |Stable|

.. raw:: html

  <div align="center">
    <h1><code>amlight/sdntrace_cp</code></h1>

    <strong> Napp that traces OpenFlow paths in the control plane</strong>

    <h3><a href="https://kytos-ng.github.io/api/sdntrace_cp.html">OpenAPI Docs</a></h3>
  </div>


Overview
========

``sdntrace_cp`` traces OpenFlow paths in the control plane. This NApp can used by either network operators to troubleshoot control plane flow entries or other NApps that might need to make sure that a control plane path is traceable.

Installing
==========

To install this NApp, first, make sure to have the same venv activated as you have ``kytos`` installed on:

.. code:: shell

   $ git clone https://github.com/kytos-ng/sdntrace_cp.git
   $ cd sdntrace_cp
   $ python setup.py develop

Requirements
============

Events
======

Subscribed
----------
.. TAGs

.. |License| image:: https://img.shields.io/github/license/kytos-ng/sdntrace_cp.svg
   :target: https://github.com/kytos-ng/sdntrace_cp/blob/master/LICENSE
.. |Build| image:: https://scrutinizer-ci.com/g/kytos-ng/sdntrace_cp/badges/build.png?b=master
  :alt: Build status
  :target: https://scrutinizer-ci.com/g/kytos-ng/sdntrace_cp/?branch=master
.. |Coverage| image:: https://scrutinizer-ci.com/g/kytos-ng/sdntrace_cp/badges/coverage.png?b=master
  :alt: Code coverage
  :target: https://scrutinizer-ci.com/g/kytos-ng/sdntrace_cp/?branch=master
.. |Quality| image:: https://scrutinizer-ci.com/g/kytos-ng/sdntrace_cp/badges/quality-score.png?b=master
  :alt: Code-quality score
  :target: https://scrutinizer-ci.com/g/kytos-ng/sdntrace_cp/?branch=master
.. |Stable| image:: https://img.shields.io/badge/stability-stable-green.svg
   :target: https://github.com/kytos-ng/sdntrace_cp
.. |Tag| image:: https://img.shields.io/github/tag/kytos-ng/sdntrace_cp.svg
   :target: https://github.com/kytos-ng/sdntrace_cp/tags
