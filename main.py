#!/usr/bin/env python


import cgi
import datetime
import re
import wsgiref.handlers


from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template


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
    self.response.out.write(template.render('templates/run.html', 
                                            {'active_run': True}))


def main():
  wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([
    ('/', MainPage),
    ('/upload', UploadModelPage),
    ('/run', RunPage)
  ]))


if __name__ == '__main__':
  main()
