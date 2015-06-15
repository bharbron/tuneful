import os.path
import json

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from jsonschema import validate, ValidationError

import models
import decorators
from tuneful import app
from database import session
from utils import upload_path

@app.route("/api/songs", methods=["GET"])
@decorators.accept("application/json")
def songs_get():
  """ get a list of songs """
  songs = session.query(models.Song)
  songs = songs.all()
  
  # Convert the songs to JSON and return a response
  data = json.dumps([song.as_dictionary() for song in songs])
  return Response(data, 200, mimetype="application/json")