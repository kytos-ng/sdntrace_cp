#########
Changelog
#########
All notable changes to the sdntrace_cp NApp will be documented in this file.

[UNRELEASED] - Under development
********************************
Added
=====

Changed
=======

Deprecated
==========

Removed
=======

Fixed
=====

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

