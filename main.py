#!/usr/bin/env python


import cgi
import datetime
import logging
import re
import wsgiref.handlers


from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template


class StochKitModelWrapper(db.Model):
  """
    A StochKitModelWrapper is a representation of the biochemical model that 
      runs with the open source StochKit2.0 software package. It contains the 
      actual model itself and will eventually be expanded to include metadata 
      about the model.
  """
  model = db.TextProperty()


class MainPage(webapp.RequestHandler):
  def get(self):
    self.response.out.write(template.render('templates/index.html', 
                                            {'active_index': True}))


class UploadModelPage(webapp.RequestHandler):
  def get(self):
    self.response.out.write(template.render('templates/upload.html', 
                                            {'active_upload': True}))


class RunPage(webapp.RequestHandler):
  def get(self):
    model_query = db.GqlQuery("SELECT * FROM StochKitModelWrapper")
    models = [model for model in model_query]
    if len(models) > 0:
      models_present = True
    else:
      models_present = False

    self.response.out.write(template.render('templates/run.html', 
                                            {'active_run': True,
                                             'models': models,
                                             'models_present': models_present}))


def main():
  logging.getLogger().setLevel(logging.DEBUG)
  wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([
    ('/', MainPage),
    ('/upload', UploadModelPage),
    ('/run', RunPage)
  ]))


if __name__ == '__main__':
  main()
