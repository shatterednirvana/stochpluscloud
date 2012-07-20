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
    self.response.out.write(template.render('templates/index.html', {}))


class RunPage(webapp.RequestHandler):
  def get(self):
    self.response.out.write(template.render('templates/run.html', {}))

def main():
  wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([
    ('/', MainPage),
    ('/run', RunPage)
  ]))


if __name__ == '__main__':
  main()
