++++++++++++++++++++++++++++
relay-examples-todo-graphene
++++++++++++++++++++++++++++

|license| |build|

.. |license| image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://en.wikipedia.org/wiki/MIT_License
   :alt: MIT Licensed

.. |build| image:: https://travis-ci.org/smbolton/relay-examples-todo-graphene.svg?branch=master
   :target: https://travis-ci.org/smbolton/relay-examples-todo-graphene
   :alt: Build Status

relay-examples-todo-graphene is a GraphQL_ backend server for the `Relay TodoMVC`_ example. It is
built using Graphene and Django.

.. _GraphQL: http://graphql.org/
.. _TodoMVC: https://github.com/relayjs/relay-examples/tree/master/todo

Installation
============

.. code:: shell

   $ git clone https://github.com/smbolton/relay-examples-todo-graphene.git
   $ cd relay-examples-todo-graphene
   $ virtualenv --python=python3 venv
   $ source venv/bin/activate
   $ pip install -r requirements.txt
   $ ./manage.py makemigrations
   $ ./manage.py migrate
   $ ./manage.py test  # all tests should pass
   $ ./manage.py runserver

The server includes the GraphiQL_ schema-browser IDE, so once you have the server running, point
your browser at:

http://localhost:8000/graphql/

and you will be able to browse the schema and submit test queries.

.. _GraphiQL: https://github.com/graphql/graphiql

License
=======
Copyright © 2017 Sean Bolton.

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
