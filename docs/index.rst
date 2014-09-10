=================
Distill Framework
=================

Distill is a minimalistic Python web framework designed to make development of Python web applications easy and quick.

Installation
============

Distill can be installed from PyPi with pip::

    $ pip install distill


Getting Started
===============

Distill uses routes to provide route matching.  Getting started with is as easy as creating a new instance of the Distill
class and mapping some routes.

.. code-block:: python

    from distill.application import Distill

    #Define a route action
    def home(request, response):
        return "Hello world"

    app = Distill()
    app.map_connect('home', '/', action=home)

The above code maps the base URL in your application to a route named "home"

When users visit your application Distill attempts to match the URL they are visiting with the routes you have mapped
using ``map_connect()``  If a matching route is found Distill then calls the action defined for that route to create a
response, and anything else returns a 404.

By default all responses are rendered as plain text, with the string returned by the action serving as the body of the
response. if you want to render your response you must use a renderer:

.. code-block:: python

    from distill.renderers import renderer

    @renderer('home.mako')
    def home(request, response):
        return {"msg": "Hello world"}

Out of the box Distill supports the Mako templating engine for rendering responses.  You'll notice that now, instead of
returning a string our action is returning a dictionary.  This dictionary represents the variables passed to the Mako engine
when it renderes your page.

Controllers
===========

Rather than defining functions and passing callables to the action parameter of ``map_connect()`` you can define controllers
and provide ``map_connect()`` with a controller and an action, where action is the name of some method on the controller class

.. code-block:: python

    from distill.application import Distill
    from distill.renderers import renderer

    #define your controller class
    class HomeController(object):

        @renderer('home.mako')
        def home(self, request, response):
            return {"msg": "Hello world"}

    app = Distill()
    app.map_connect('home', '/', controller='homecontroller', action='home')
    #now register your controller with Distill
    app.add_controller('homecontroller', HomeController)


