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

@app.route("/api/songs", methods=["POST"])
@decorators.accept("/application/json")
def song_post():
  """ add a new song """
  data = request.json
  
  # Get the file from the database
  file = session.query(models.File).get(data["file"]["id"])
  
  # If the file does not exist, respond with a 404
  if not file:
    message = "Could not find file with id {}".format(data["file"]["id"])
    data = json.dumps({"message": message})
    return Response(data, 404, mimetype="application/json")
    
  
  # Add the new song to the database
  song = models.Song(file=file)
  session.add(song)
  session.commit()
  
  # Return a 201 Created, containing the song as json
  data = json.dumps(song.as_dictionary())
  return Response(data, 201, mimetype="application/json")