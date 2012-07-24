#!/usr/bin/env python


import cgi
import datetime
import json
import logging
import re
import urllib
import wsgiref.handlers


from google.appengine.api import users
from google.appengine.api import urlfetch


from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template


class StochKitModelWrapper(db.Model):
  """
    A StochKitModelWrapper is a representation of the biochemical model that 
      runs with the open source StochKit2.0 software package. It contains the 
      actual model itself and will eventually be expanded to include metadata 
      about the model. Models also have a name - this is stored and referenced
      as the keyname, to avoid the unnecessary cost of indexing it.
  """
  model = db.TextProperty()


class MainPage(webapp.RequestHandler):
  def get(self):
    self.response.out.write(template.render('templates/index.html', 
                                            {'active_index': True}))


class ModelREST(webapp.RequestHandler):
  """
    ModelREST provides a RESTful interface to StochKitModelWrappers in the
      Datastore. HTTP methods are exposed to get, create (via POST), and delete
      models. All methods here return JSON dicts with a 'success' parameter
      that callers can use to verify that their call succeeded, and a 'reason'
      parameter that explains why their call may not have succeeded.
  """


  def get(self):
    """
      Gets a StochKitModelWrapper from the Datastore, referenced by the model's
        name.
    """
    name = self.request.get('name')
    if not name:
      result = {'success': False, 'reason': 'Name not specified.'}
      self.response.out.write(json.dumps(result))
      return
    
    try:
      model_wrapper = StochKitModelWrapper.get_by_key_name(name)
      if not model_wrapper:
        result = {'success': False, 'reason': 'Model not found.'}
        self.response.out.write(json.dumps(result))
        return
    except:
      result = {'success': False, 'reason': 'Datastore error'}
      self.response.out.write(json.dumps(result))
      return

    result = {'success':True, 'model': model_wrapper.model}
    self.response.out.write(json.dumps(result))
    return


  def post(self):
    """
      Creates a new StochKitModelWrapper and stores it in the Datastore.
        Requires the name and model to be specified as parameters.
    """
    result = create_model(self.request.get('name'), self.request.get('model'))
    self.response.out.write(json.dumps(result))


  def delete(self):
    """
      Deletes the specified model from the Datastore. Requires the model name
        to be specified, and succeeds if (1) the name is specified, (2) the name
        refers to a model that exists, and (3) there are no problems deleting
        the model from the Datastore.
    """
    name = self.request.get('name')
    if not name:
      result = {'success': False, 'reason': 'Name not specified.'}
      self.response.out.write(json.dumps(result))
      return
    
    try:
      model = StochKitModelWrapper.get_by_key_name(name)
      if not model:
        result = {'success': False, 'reason': 'Model not found.'}
        self.response.out.write(json.dumps(result))
        return

      model.delete()
      result = {'success': True}
      self.response.out.write(json.dumps(result))
      return
    except:
      result = {'success': False, 'reason': 'Datastore error.'}
      self.response.out.write(json.dumps(result))
      return


class UploadModelPage(webapp.RequestHandler):
  """
    Provides a web UI around POST /model, to allow users to create
      StochKitModelWrappers via the web interface instead of the RESTful one.
  """


  def get(self):
    self.response.out.write(template.render('templates/upload.html', 
                                            {'active_upload': True}))


  def post(self):
    result = create_model(self.request.get('name'), self.request.get('model'))
    if result['success']:
      self.response.out.write(template.render('templates/uploaded.html',
                                              {'active_upload': True}))
    else:
      self.response.out.write(template.render('templates/upload.html',
                                              {'active_upload': True,
                                              'error': result['reason']}))


class RunPage(webapp.RequestHandler):
  """
    Lets users run simulations via StochKit2.0 once they have uploaded and
      stored a model in the Datastore.
  """

  def get(self):
    model_query = db.GqlQuery("SELECT * FROM StochKitModelWrapper")
    model_names = [model.key().name() for model in model_query]
    if len(model_names) > 0:
      models_present = True
    else:
      models_present = False

    self.response.out.write(template.render('templates/run.html', 
                                            {'active_run': True,
                                             'models': model_names,
                                             'models_present': models_present}))


  def post(self):
    # get each param
    keep_trajectories = self.request.get('keep-trajectories')
    logging.debug("keep trajectories? %s" % keep_trajectories)


def create_model(name, model):
  """
    Creates a new StochKitModelWrapper and stores it in the Datastore.

    Arguments:
      name: A str that is used to identify the given model.
      model: A str whose contents are the model to simulate.

    Returns:
      A dict that indicates whether or not the model was created successfully,
        and a reason why the model could not be created (if applicable).
  """
  if not name:
    return {'success': False, 'reason': 'Name not specified.'}

  if not model:
    return {'success': False, 'reason': 'Model not specified.'}

  try:
    model_wrapper = StochKitModelWrapper(key_name=name)
    model_wrapper.model = model
    model_wrapper.put()
    return {'success': True}
  except:
    return {'success': False, 'reason': 'Datastore error.'}


def main():
  logging.getLogger().setLevel(logging.DEBUG)
  wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([
    ('/', MainPage),
    ('/model', ModelREST),
    ('/upload', UploadModelPage),
    ('/run', RunPage)
  ]))


if __name__ == '__main__':
  main()
