mqtt2measurinator
========

CLI tool for forwarding Nokeval MTR wireless transmitter readings from MQTT server to measurinator api
Preparing the Development
-------------------------

1. Ensure ``pip`` and ``pipenv`` are installed.
2. Clone repository ``git clone git @github.com:tvallas/mqtt2measurinator``
3. ``cd`` into the repository.
4. Fetch development dependencies ``make install``
5. Activate virtualenv: ``pipenv shell``

Usage
-----

Pass in measurinator client id, secret key and mqtt server address

example

::

    $ mqtt2measurinator  --mqtt-host 192.168.1.2 --client_id xxxxx --key yyyyy


