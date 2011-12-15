from __future__ import absolute_import

from flask import Flask
from flask.ext.script import Manager
from flask.ext.celery import install_commands as install_celery_commands

app = Flask(__name__)
manager = Manager(app)
install_celery_commands(manager)

if __name__ == "__main__":
	import sys
	import os
	#need to append helppme's path to sys.path, so celery can import the 
	#required and register the proper task modules
	sys.path.append(os.path.dirname(os.getcwd()))
	manager.run()