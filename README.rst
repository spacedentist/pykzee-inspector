pykzee-inspector
================

A plug-in for Pykzee that launches a web server, serving a browser application for inspecting the Pykzee state.

Installation
------------

.. code-block:: shell-session

   pip install pykzee-inspector

Then, add this object somewhere in your Pykzee configuration:

.. code-block:: json

   {
     "__plugin__": "pykzee.inspector.InspectorPlugin",
     "port": 8000
   }

Open ``http://localhost:8000`` in a web browser to see the whole Pykzee state.
