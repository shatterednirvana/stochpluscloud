#!/usr/bin/env python


import cgi
import datetime

try:
  import json
except ImportError:
  from django.utils import simplejson as json

import logging
import re
import urllib
import wsgiref.handlers


from google.appengine.api import taskqueue
from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api.appscale import babel
from google.appengine.api.appscale import neptune


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


class EnsembleResultWrapper(db.Model):
  """
    An EnsembleResultWrapper is a representation of the results produced by
      running a StochKit ensemble. Typically this produces a series of averages
      and variances. params refers to the babel-produced metadata that indicates
      where the standard output, standard error, and profiling information is
      stored, and results are the averages and variances produced by the
      simulation (typically saved to standard output). Finally, model refers to
      the model that was used to generate these results.

      TODO(cgb): Should we reference the model itself or just say the name?
      TODO(cgb): Should we include the parameters used to generate the results?
  """
  params = db.TextProperty()
  results = db.TextProperty()


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


class ResultREST(webapp.RequestHandler):
  def get(self):
    name = self.request.get('name')
    if not name:
      result = {'success': False, 'reason': 'Name not specified'}
      self.response.out.write(json.dumps(result))
      return

    try:
      ensemble_wrapper = EnsembleResultWrapper.get_by_key_name(name)
      if not ensemble_wrapper:
        result = {'success': False, 'reason': 'Result not found.'}
        self.response.out.write(json.dumps(result))
        return

      try:
        result = ensemble_wrapper.result
      except AttributeError:
        result = babel.get_output(ensemble_wrapper.params)
        ensemble_wrapper.result = result
        ensemble_wrapper.put()

      result = {'success': True, 'result': ensemble_wrapper.result}
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
    """
      Lists all the uploaded models on a web page so that the user can pick
        which one should be used to run their simulations.
    """

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
    """
      Runs StochKit2.0 via babel, with the arguments passed in via the web UI.
    """
    encoded_params = self.request.get('parameters')

    params = json.loads(encoded_params)
    # TODO(cgb): validate this
    output = params['output']
    model = params['model']
    time = params['time']
    realizations = params['realizations']
    keep_trajectories = params['keep-trajectories']
    keep_histograms = params['keep-histograms']
    label = params['label']
    seed = params['seed']
    epsilon = params['epsilon']
    threshold = params['threshold']
    where_to_run = params['where_to_run']

    model_wrapper = StochKitModelWrapper.get_by_key_name(model)
    model_contents = model_wrapper.model
    model_file_location = neptune.write_neptune_job_code(model_contents)

    args = []
    args.append('--model')
    args.append(model_file_location)

    args.append('--time')
    args.append(time)

    args.append('--realizations')
    args.append(realizations)

    if keep_trajectories:
      args.append('--keep-trajectories')

    if keep_histograms:
      args.append('--keep-histograms')

    if label:
      args.append('--label')

    args.append('--seed')
    args.append(seed)

    args.append('--epsilon')
    args.append(epsilon)

    args.append('--threshold')
    args.append(threshold)

    bash_script_contents = """#!/bin/bash
/usr/local/StochKit2.0/ssa $@ --out-dir /tmp/baz/ --force
cat /tmp/baz/stats/means.txt
cat /tmp/baz/stats/variances.txt
"""
    bash_script_location = neptune.write_neptune_job_code(bash_script_contents)

    params = {
      ':code': bash_script_location,
      ':argv': args,
      ':bucket_name': "neptune-testbin",
      ':executable': "bash",
      ':storage': "s3",
      ':EC2_ACCESS_KEY': "your access key",
      ':EC2_SECRET_KEY': "your secret key",
      ':S3_URL': 'https://s3.amazonaws.com/'
    }
    job_result = babel.run_job(params)

    # TODO(cgb): remove the files we wrote to run the babel job

    result = EnsembleResultWrapper(key_name = output)
    result.params = json.dumps(job_result)
    result.put()

    # Prepopulate the result in the background, once the job finishes.
    taskqueue.add(url='/result', params={'name': output}, method='GET')

    self.response.out.write(json.dumps({'success':True}))



class ViewPage(webapp.RequestHandler):

  
  def get(self):
    result_query = db.GqlQuery("SELECT * FROM EnsembleResultWrapper")
    result_names = [result.key().name() for result in result_query]
    if len(result_names) > 0:
      results_present = True
    else:
      results_present = False

    self.response.out.write(template.render('templates/view.html', 
                                            {'active_view': True,
                                             'results_present': results_present,
                                             'results': result_names}))


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
    ('/result', ResultREST),
    ('/upload', UploadModelPage),
    ('/run', RunPage),
    ('/view', ViewPage)
  ]))


if __name__ == '__main__':
  main()
