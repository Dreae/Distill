=================
Distill Framework
=================

Distill is a minimalistic Python web framework designed to make development of Python web applications easy and quick.

Installation
============

Distill can be installed from PyPi with pip::

    $ pip install distill-framework


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

Middleware
==========

You can define multiple middleware that will be called either before or after the action registered for a response

There are two main ways of registering middleware, either passing a callable to ``app.use()``, which will register a middleware
to be used for every request, or using the before or after decorator, which will only affect requests that use the decorated
method

.. code-block:: python

    from distill.application import Distill

    def before_middleware(request, response):
        print("This method will be called before every request")

    def after_middleware(request, response):
        print("This method will be called after every request")

    app = Distill()
    app.use(before_middleware)
    app.use(after_middleware, before=False)

Using ``app.use()`` you can define multiple middleware, which will be called in succession based on the order they are
added

.. code-block:: python

    from distill.application import Distill

    def first_before(request, response):
        print("This method will be called first before every request")

    def second_before(request, response):
        print("This method will be called second before every request")

    app = Distill()
    app.use(first_before)
    app.use(second_before)

Or using the decorator method:

.. code-block:: python

    from distill.application import Distill
    from distill.decorators import before, after

    def on_before(request, response):
        print("This method will be called before the home method")

    def on_after(request, response):
        print("This method will be called after the home method")

    @before(on_before)
    @after(on_after)
    def home(request, response):
        return "Hello world"

    app = Distill()
    app.map_connect('home', '/', action=home)

*Note: As of Distill 0.1.3 you may modify the response object in middleware, but the return value is ignored*

Handling Exceptions
===================

Distill allows you to define methods that will handle any exceptions your app may encounter.  This allows you to generate
customized error pages to display to users, or to sepecify custom logic to be executed in the event of an error.

Defining an error handler is simple:

.. code-block:: python

    from distill.application import Distill
    from distill.exceptions import HTTPNotFound
    from distill.renderers import renderer

    @renderer('404.mako')
    def on_404(request, response):
        # Exception handlers behave exactly like
        # request methods
        return {'msg': "Whoops, page not found"}

    app = Distill()
    app.on_except(HTTPNoFound, on_404)

Note that by default the response will contain the HTTP status code for the encountered error.  If this is undesirable
you can modify the response directly, or return a new response:

.. code-block:: python

    @renderer('404.mako')
    def on_404(request, response):
        # This handler will set the HTTP status
        # code to 200 rather than returning a
        # 404 to the client
        response.status = "200 OK"
        return {'msg': "Whoops, page not found"}

    def on_401(request, response):
        # Useful for redirecting users to authenticate
        return HTTPFound(location='https://yoursite/login')
