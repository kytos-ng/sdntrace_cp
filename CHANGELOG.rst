#########
Changelog
#########
All notable changes to the sdntrace_cp NApp will be documented in this file.

[UNRELEASED] - Under development
********************************

[2023.1.0] - 2023-06-12
***********************

Added
=====
- Support ``"untagged"`` and ``"any"`` on EVCs.
- ``PUT /trace and /traces`` endpoints validate payload with ``@validate_openapi``

Changed
=======
- Update ``tracepath`` to support the trace type: ``loop``. Other three types are ``starting`` for the first trace_step, ``intermediary`` for subsequent trace_steps (previously ``trace``), and ``last`` for a terminating last switch where a flow lookup matched.
- Add new case of ``loop`` when the outgoing interface is the same as the input interface.
- Remove ``last_id`` and ``traces`` parameters
- Remove ``GET /api/amlight/sdntrace_cp/trace/{trace_id}`` in ``openapi.yml``
- ``v1`` prefix was added on the API routes to stabilize this NApp.

Fixed
=====
- Check the ``actions`` field in flows when running a trace to avoid ``KeyError``.
- In ``PUT /trace`` and ``PUT /traces``, field ``switch``` is defined as required, as well as its parameters ``dpid``` and ``in_port``.
- Check that an interface has been found with ``find_endpoint`` given ``switch`` and ``port`` at each ``trace_step``.

Removed
=======

- Removed ``TRIGGER_SCHEDULE_TRACES``, ``TRIGGER_IMPORTANT_CIRCUITS`` and ``FIND_CIRCUITS_IN_FLOWS`` from settings.
- Removed ``automate`` in ``main``.
- Removed ``update_circuits`` functionality in ``main``. 
- Removed the dependency on ``apscheduler``.

General Information
===================
- ``@rest`` endpoints are now run by ``starlette/uvicorn`` instead of ``flask/werkzeug``.

[2022.3.1] - 2023-02-27
***********************

Changed
=======
- ``PUT /traces`` will return the results in order, without aggregating them by `dpid`. Also, failed traces are not omitted.

[2022.3.0] - 2022-12-15
***********************

Added
=====
- Added ``apscheduler`` library to handle job scheduling
- Added ``PUT /traces`` endpoint for bulk requests
- Added output port information to the trace result (last step) to help validating intra-switch EVCs

Changed
=======
- The functionality ``match_and_aply`` has been added to match flows and apply actions. This matches a given packet against the stored flows.

Removed
=======
- Removed dependency from ``amlight/scheduler``
- Removed support for OpenFlow 1.0
- Unsubscribe to the `amlight/flow_stats.flows_updated` event
- Dependency on ``flow_stats`` has been removed, from where the functionality ``match_and_aply`` was previously used.

Security
========

[2022.2.1] - 2022-08-15
***********************

Fixed
=====
- Made a shallow copy when iterating on shared data structure to avoid RuntimeError size changed


[2022.2.0] - 2022-08-08
***********************

Fixed
=====
- [Issue 25] Fix tracepath results to display correct vlan id when using Q-in-Q

General Information
===================
- Increased unit test coverage to at least 85%

[2022.1.0] - 2022-02-08
***********************

Added
=====
- Added ``FIND_CIRCUITS_IN_FLOWS`` settings option to enable or disable the feature to trigger the ``find_circuits`` routine
- Enhanced and standardized setup.py `install_requires` to install pinned dependencies
- [Issue 5] Add setup.py and requirements

Fixed
=====
- [Issue 6] Fix comparison of endpoints when an endpoint does not provide all necessary fields
- [Issue 8] Change log level of run_traces results to debug

