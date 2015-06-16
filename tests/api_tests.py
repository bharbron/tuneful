import unittest
import os
import shutil
import json
from urlparse import urlparse
from StringIO import StringIO

import sys; print sys.modules.keys()

# Configure our app to use the testing databse
# But first check to see if we're already running using the Travis-CI config
if "CONFIG_PATH" not in os.environ or os.environ["CONFIG_PATH"] != "tuneful.config.TravisConfig":
  os.environ["CONFIG_PATH"] = "tuneful.config.TestingConfig"

from tuneful import app
from tuneful import models
from tuneful.utils import upload_path
from tuneful.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the tuneful API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

        # Create folder for test uploads
        os.mkdir(upload_path())

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

        # Delete test upload folder
        shutil.rmtree(upload_path())

    def testGetEmptySongs(self):
      """ Get a song from an empty database """
      response = self.client.get("/api/songs", headers=[("Accept", "application/json")])
      
      self.assertEqual(response.status_code, 200)
      self.assertEqual(response.mimetype, "application/json")
      
      data = json.loads(response.data)
      self.assertEqual(data, [])

    def testGetSongs(self):
      """ Get songs from a populated database """
      fileA = models.File(name="FileA.mp3")
      fileB = models.File(name="FileB.mp3")
      songA = models.Song(file=fileA)
      songB = models.Song(file=fileB)
      
      session.add_all([fileA, fileB, songA, songB])
      session.commit
      
      response = self.client.get("/api/songs", headers=[("Accept", "application/json")])
      
      self.assertEqual(response.status_code, 200)
      self.assertEqual(response.mimetype, "application/json")
      
      data = json.loads(response.data)
      self.assertEqual(len(data), 2)
      
      songA = data[0]
      self.assertEqual(songA, {"id": 1, "file": {"id": 1, "name": "FileA.mp3"}})
      
      songB = data[1]
      self.assertEqual(songB, {"id": 2, "file": {"id": 2, "name": "FileB.mp3"}})
      
    def testUnsupportedAcceptHeader(self):
      """ Try to get songs using a unsupported mimetype """
      response = self.client.get("/api/songs", headers=[("Accept", "application/xml")])
      
      self.assertEqual(response.status_code, 406)
      self.assertEqual(response.mimetype, "application/json")
      
      data = json.loads(response.data)
      self.assertEqual(data["message"], "Request must accept application/json data")
      
    def testGetSingleSong(self):
      """ Get a single song """
      fileA = models.File(name = "FileA.mp3")
      fileB = models.File(name = "FileB.mp3")
      songA = models.Song(file=fileA)
      songB = models.Song(file=fileB)
      
      session.add_all([fileA, fileB, songA, songB])
      session.commit()
      
      response = self.client.get("/api/songs/2", headers=[("Accept", "application/json")])
      
      self.assertEqual(response.status_code, 200)
      self.assertEqual(response.mimetype, "application/json")
      
      song = json.loads(response.data)
      self.assertEqual(song, {"id": 2, "file": {"id": 2, "name": "FileB.mp3"}}) 
      
    def testPostSong(self):
      """ Add a new song """
      # Add a file to the database to test against
      fileA = models.File(name="FileA.mp3")
      
      session.add(fileA)
      session.commit()
      
      data = json.dumps({"file": {"id": 1}})
      response = self.client.post("/api/songs",
                                  data=data,
                                  content_type="application/json",
                                  headers=[("Accept", "application/json")]
                                 )
      
      self.assertEqual(response.status_code, 201)
      self.assertEqual(response.mimetype, "application/json")
      #self.assertEqual(urlparse(response.headers.get("Location")).path, "/api/songs")
      
      data = json.loads(response.data)
      self.assertEqual(data, {"id": 1, "file": {"id": 1, "name": "FileA.mp3"}})
      
      songs = session.query(models.Song).all()
      self.assertEqual(len(songs), 1)
      
      song = songs[0]
      self.assertEqual(song.as_dictionary(), {"id": 1, "file": {"id": 1, "name": "FileA.mp3"}})
      
    def testPostSongNonexistentFile(self):
      """ Trying to add a new song when the referenced file id does not exist """
      data = json.dumps({"file": {"id": 1}})
      response = self.client.post("/api/songs",
                                 data=data,
                                 content_type="application/json",
                                 headers=[("Accept", "application/json")]
                                 )
      
      self.assertEqual(response.status_code, 404)
      self.assertEqual(response.mimetype, "application/json")
      
      data = json.loads(response.data)
      self.assertEqual(data["message"], "Could not find file with id 1")
      
    def testPostSongInvalidData(self):
      """ Trying to add a new song but passing invalid data """
      fileA = models.File(name = "FileA.mp3")
      
      session.add(fileA)
      session.commit()
      
      data = json.dumps({"file": {"id": "invaliddata"}})
      response = self.client.post("/api/songs",
                                 data=data,
                                 content_type="application/json",
                                 headers=[("Accept", "application/json")]
                                 )
      
      self.assertEqual(response.status_code, 422)
      
      data = json.loads(response.data)
      self.assertEqual(data["message"], "u'invaliddata' is not of type 'integer'")
      
    def testPostSongMissingData(self):
      """ Trying to add a new song but missing the file id """
      fileA = models.File(name = "FileA.mp3")
      
      session.add(fileA)
      session.commit()
      
      data = json.dumps({"file": {}})
      response = self.client.post("/api/songs",
                                 data=data,
                                 content_type="application/json",
                                 headers=[("Accept", "application/json")]
                                 )
      
      self.assertEqual(response.status_code, 422)
      self.assertEqual(response.mimetype, "application/json")
      
      data = json.loads(response.data)
      self.assertEqual(data["message"], "'id' is a required property")
      
    def testPostUnsupportedMimetype(self):
      """ Try to add a new song with the wrong mimetype """
      data = "<xml></xml>"
      response = self.client.post("/api/songs",
                                 data=data,
                                 content_type="application/xml",
                                 headers=[("Accept", "application/json")]
                                 )
      
      self.assertEqual(response.status_code, 415)
      self.assertEqual(response.mimetype, "application/json")
      
      data = json.loads(response.data)
      self.assertEqual(data["message"], "Request must contain application/json data")
                                          
                                        
      
if __name__ == "__main__":
    unittest.main()
