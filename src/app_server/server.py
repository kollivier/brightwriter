import logging
import os
import subprocess
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

@flaskapp.route('/openInApplication')
def open_in_application():
    filename = request.args.get('filename')
    if sys.platform.startswith('darwin'):
        subprocess.call(['open', filename])

    return jsonify({'success': True})

@flaskapp.route('/<path:path>')
def catch_all(path):
    if path.startswith('app/'):
        path = path.replace('app', os.path.join(settings.AppDir, 'gui', 'html'))
        return send_file(path, cache_timeout=0)
    full_path = os.path.abspath(os.path.join(settings.ProjectDir, path))
    if os.path.exists(full_path):
        return send_file(full_path, cache_timeout=0)
    else:
        try:
            return send_file(os.path.join(static_dir, path), cache_timeout=0)
        except IOError:
            abort(404)

def start_server():
    logging.info("Calling start_server...")
    global flaskthread
    flaskthread = pew.ui.PEWThread(target=flaskapp.run, args=('0.0.0.0', SERVER_PORT))
    flaskthread.daemon = True
    flaskthread.start()
