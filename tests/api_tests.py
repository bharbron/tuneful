import unittest
import os
import shutil
import json
from urlparse import urlparse
from StringIO import StringIO

import sys; print sys.modules.keys()
# Configure our app to use the testing databse
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
      response = self.client.get("/api/songs", headers=[("Accept", "application/xml")])
      
      self.assertEqual(response.status_code, 406)
      self.assertEqual(response.mimetype, "application/json")
      
      data = json.loads(response.data)
      self.assertEqual(data["message"], "Request must accept application/json data")
