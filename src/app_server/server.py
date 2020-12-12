import logging
import os
import sys

import settings

import pew
import pew.ui

from flask import abort, Flask, jsonify, request, send_file

from .constants import SERVER_PORT

thisdir = os.path.dirname(os.path.abspath(__file__))

if hasattr(sys, 'frozen'):
    thisdir = os.path.dirname(sys.argv[0])

static_dir = os.path.join(thisdir, 'frontend')

flaskapp = Flask(__name__)
flaskthread = None


@flaskapp.route('/<path:path>')
def catch_all(path):
    full_path = os.path.abspath(os.path.join(settings.ProjectDir, path))
    if os.path.exists(full_path):
        return send_file(full_path)
    else:
        try:
            return send_file(os.path.join(static_dir, path))
        except IOError:
            abort(404)

def start_server():
    logging.info("Calling start_server...")
    global flaskthread
    flaskthread = pew.ui.PEWThread(target=flaskapp.run, args=('0.0.0.0', SERVER_PORT))
    flaskthread.daemon = True
    flaskthread.start()
