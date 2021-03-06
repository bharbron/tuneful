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

# JSON Schema describing the structure of a post
song_schema = {
  "properties": {
    "file" : {
      "properties": {
        "id" : {
          "type": "integer"
        }
      },
      "required": ["id"]
    }
  },
  "required": ["file"]
}

@app.route("/api/songs", methods=["GET"])
@decorators.accept("application/json")
def songs_get():
  """ get a list of songs """
  songs = session.query(models.Song)
  songs = songs.all()
  
  # Convert the songs to JSON and return a response
  data = json.dumps([song.as_dictionary() for song in songs])
  return Response(data, 200, mimetype="application/json")

@app.route("/api/songs/<int:id>", methods=["GET"])
@decorators.accept("application/json")
def song_get(id):
  """ get a single song """
  song = session.query(models.Song).get(id)
  
  # If that song doesn't exist, return a 404 with a helpful message
  if not song:
    message = "Could not find song with id {}".format(id)
    data = json.dumps({"message": message})
    return Response(data, 404, mimetype="application/json")
  
  # Convert the song to JSON and return a response
  data = json.dumps(song.as_dictionary())
  return Response(data, 200, mimetype="application/json")

@app.route("/api/songs", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def song_post():
  """ add a new song """
  data = request.json
  
  # Check that the JSON supplied is valid
  # If not you return a 422 Unprocessable Entity
  try:
    validate(data, song_schema)
  except ValidationError as error:
    data = {"message": error.message}
    return Response(json.dumps(data), 422, mimetype="application/json")
  
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
  headers = {"Location": url_for("song_get", id=song.id)}
  return Response(data, 201, headers=headers, mimetype="application/json")

@app.route("/uploads/<filename>", methods=["GET"])
def uploaded_file(filename):
  return send_from_directory(upload_path(), filename)

@app.route("/api/files", methods=["POST"])
@decorators.require("multipart/form-data")
@decorators.accept("application/json")
def file_post():
  file = request.files.get("file")
  if not file:
    data = {"message": "Could not find file data"}
    return Response(json.dumps(data), 422, mimetype="application/json")
  
  filename = secure_filename(file.filename)
  db_file = models.File(filename=filename)
  session.add(db_file)
  session.commit()
  file.save(upload_path(filename))
  
  data = db_file.as_dictionary()
  return Response(json.dumps(data), 201, mimetype="application/json")
