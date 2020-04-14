python_awair
========================================

*python_awair* is an asyncio client for the Awair_ REST API_.

The main goal of the project is to provide a useful, object-oriented
client, rather than a thin veneer over the underlying API. A secondary
goal is to support the Home Assistant integration_, though the project
wishes to be useful to all.

Currently, the project supports:

* Fetching user information, devices owned by a user, and API usage information
* Retreiving current, summary, and raw air quality information for the *user* devices

Planned features:

* Supporting the *user* device management API
* Supporting the *organization* API

This library is considered active and supported by its author, and PRs or issues are
gladly accepted.

Getting started
---------------

Install *python_awair* from pip::

  $ pip install python_awair

You'll need an access token for the Awair API, which you can obtain from the `developer portal`_.

.. _Awair: https://getawair.com
.. _API: https://docs.developer.getawair.com/?version=latest
.. _integration: https://www.home-assistant.io/integrations/awair/
.. _`developer portal`: https://developer.getawair.com

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   examples.rst
   python_awair.rst


* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
