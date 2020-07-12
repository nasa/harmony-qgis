from datetime import datetime
from time import sleep
import json

import http.client as http_client
import logging

import tempfile
import os
import requests

from qgis.core import Qgis, QgsApplication, QgsProcessingFeedback, QgsProcessingContext, QgsTaskManager, QgsTask, QgsProject, QgsSettings, QgsVectorLayer, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsRasterLayer, QgsMessageLog

# Session accessible by callers
session = requests.session()

def debug_http():
  """Adds debugging output to HTTP requests to show redirects, headers, etc
  """
  http_client.HTTPConnection.debuglevel = 1
  logging.basicConfig()
  logging.getLogger().setLevel(logging.DEBUG)
  requests_log = logging.getLogger("requests.packages.urllib3")
  requests_log.setLevel(logging.DEBUG)
  requests_log.propagate = True

def request(*args, **kwargs):
  """Thin wrapper around requests.Request, logging URL sent and Content-Type received

  See https://requests.readthedocs.io/en/master/api/#requests.Request for args

  Returns:
      requests.Response -- The response to the request
  """
  req = requests.Request(*args, **kwargs)
  prepped = session.prepare_request(req)

  print('%s %s' % (prepped.method, prepped.path_url))
  response = session.send(prepped)
  print('Received %s' % (response.headers.get('Content-Type', 'unknown content',)))
  return response

def get(*args, **kwargs):
  """Performs a GET request using the request wrapper

  See https://requests.readthedocs.io/en/master/api/#requests.Request for args

  Returns:
      requests.Response -- The response to the request
  """
  return request('GET', *args, **kwargs)

def post(*args, **kwargs):
  """Performs a POST request using the request wrapper

  See https://requests.readthedocs.io/en/master/api/#requests.Request for args

  Returns:
      requests.Response -- The response to the request
  """
  return request('POST', *args, **kwargs)

def get_data_urls(response):
  """Returns the data URLs in an async response

  Arguments:
      response {response.Response} -- The async job response

  Returns:
      string[] -- An array of URLs for data links
  """
  print(response.json())
  return [link['href'] for link in response.json()['links'] if link.get('rel', 'data') == 'data']

def show(iface, response, layerName):
  QgsMessageLog.logMessage('Adding layer' + layerName, 'Harmony Plugin')
  filename = '/tmp/harmony_output_image' + layerName + '.tif'
  with open(filename, 'wb') as fd:
    for chunk in response.iter_content(chunk_size=128):
      fd.write(chunk)
  iface.addRasterLayer(filename, layerName)
  # os.remove(filename)

def worker(task, response, count):
  progress = 100.0 * count / 5.0
  task.setProgress(progress)
  body = response.json()
  QgsMessageLog.logMessage(json.dumps(body), 'Harmony Plugin')
  QgsMessageLog.logMessage('Working...', 'Harmony Plugin')
  QgsMessageLog.logMessage('Count = {}'.format(count), 'Harmony Plugin')
  sleep(5)
  count = count + 1
  status = 'working'
  if count == 5:
    QgsMessageLog.logMessage('Last worker done', 'Harmony Plugin')
    status = 'done'
  else:
    QgsMessageLog.logMessage('Worker done', 'Harmony Plugin')
    
  return { 'count': count, 'status': status, 'response': response }

def completed(exception, result=None):
  """Called when the worker tasks complete
    Arguments:
      exception {Exception} -- if an error occurs
      result {} - the response from  the worker task
  """
  QgsMessageLog.logMessage('Handling worker completion', 'Harmony Plugin')
  if exception is None:
    if result is None:
      QgsMessageLog.logMessage('Completed with no error and no result', 'Harmony Plugin')
    else:
      QgsMessageLog.logMessage(
                'Task completed',
                'Harmony Plugin')
      count = result['count']
      status = result['status']
      if status != 'done':
        QgsMessageLog.logMessage('Starting next worker', 'Harmony Plugin')
        response = result['response']
        task = QgsTask.fromFunction('Worker', worker, on_finished=completed, response=response, count=count)
        globals()['task'] = task
        QgsApplication.taskManager().addTask(globals()['task'])
        # QgsApplication.taskManager().addTask(task)
      else:
        QgsMessageLog.logMessage('Completed with no errors')
  else:
    QgsMessageLog.logMessage("Exception: {}".format(exception), 'Harmony Plugin')
    raise exception

def show_async(iface, response):
  """Shows an asynchronous Harmony response.

  Polls the output, displaying it as it changes, displaying any http data
  links in the response as they arrive, and ultimately ending once the request
  is successful or failed

  Arguments:
      response {response.Response} -- the response to display

  Returns:
      response.Response -- the response from the final successful or failed poll
  """
  def show_response(iface, response, link_count):
    QgsMessageLog.logMessage(json.dumps(response.json(), indent=2), 'Harmony Plugin')
    links = get_data_urls(response)
    new_links = links[slice(link_count, None)]
    for link in new_links:
      if link.startswith('http'):
        lastSlash = link.rindex('/')
        layerName = link[lastSlash + 1:]
        extensionIndex = layerName.rindex('.')
        if extensionIndex >= 0:
          layerName = layerName[0:extensionIndex]
        show(iface, get(link), layerName)
    return len(links)

  displayed_link_count = 0
  body = response.json()
  displayed_link_count = show_response(iface, response, displayed_link_count)
  waiting_message_printed = False
  while body['status'] not in ['successful', 'failed']:
    if not waiting_message_printed:
      QgsMessageLog.logMessage('Waiting for updates...', 'Harmony Plugin')
      waiting_message_printed = True
    sleep(1)
    progress = body['progress']
    status = body['status']
    response = session.get(response.url)
    body = response.json()
    if progress != body['progress'] or status != body['status']:
      displayed_link_count = show_response(iface, response, displayed_link_count)
      waiting_message_printed = False
  QgsMessageLog.logMessage('Async request is complete', 'Harmony Plugin')
  return response

def handleAsyncResponse(iface, response):
  # show_async(iface, response)
  QgsMessageLog.logMessage('Async request started', 'Harmony Plugin')
  task = QgsTask.fromFunction('Worker', worker, on_finished=completed, response=response, count=1)
  globals()['task'] = task
  QgsApplication.taskManager().addTask(globals()['task'])
  QgsMessageLog.logMessage('Workers started', 'Harmony Plugin')

def handleSyncResponse(iface, response, layerName, variable):
  with open('/tmp/harmony_output_image.tif', 'wb') as fd:
    for chunk in response.iter_content(chunk_size=128):
      fd.write(chunk)

  iface.addRasterLayer('/tmp/harmony_output_image.tif', layerName + '-' + variable)

def handleHarmonyResponse(iface, response, layerName, variable):
  content_type = response.headers['Content-Type']
  message = 'Content-type is: ' + content_type
  QgsMessageLog.logMessage(message, 'Harmony Plugin')

  if content_type == 'application/json; charset=utf-8':
    handleAsyncResponse(iface, response)
  else:
    handleSyncResponse(iface, response, layerName, variable)
