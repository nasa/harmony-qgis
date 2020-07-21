from datetime import datetime
from time import sleep
from pathlib import Path
import json
import http.client as http_client
import logging
import tempfile
import os
import requests

from qgis.core import Qgis, QgsApplication, QgsProject, QgsProcessingFeedback, QgsProcessingContext, QgsSettings, QgsTaskManager, QgsTask, QgsProject, QgsSettings, QgsVectorLayer, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsRasterLayer, QgsMessageLog

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

def download_image(response, layerName):
  settings = QgsSettings()
  directory = settings.value("harmony_qgis/download_dir")
  Path(directory).mkdir(parents=True, exist_ok=True)
  filename = directory + os.path.sep + 'harmony_output_image' + layerName + '.tif'
  with open(filename, 'wb') as fd:
    for chunk in response.iter_content(chunk_size=128):
      fd.write(chunk)
  return filename

def pollResults(task, iface, response, link_count):
  body = response.json()
  QgsMessageLog.logMessage(json.dumps(body), 'Harmony Plugin')
  progress = int(body['progress'])
  task.setProgress(progress)
  links = get_data_urls(response)
  new_links = links[slice(link_count, None)]
  new_layers = []
  link_count = len(links)

  for link in new_links:
      if link.startswith('http'):
        lastSlash = link.rindex('/')
        layerName = link[lastSlash + 1:]
        extensionIndex = layerName.rindex('.')
        if extensionIndex >= 0:
          layerName = layerName[0:extensionIndex]
        fileName = download_image(get(link), layerName)
        new_layers.append((layerName, fileName))

  status = body['status']
  if status not in ['successful', 'failed']:
    sleep(1)
    response = session.get(response.url)
  else:
    status = 'done'
  return { 'iface': iface, 'response': response, 'status': status, 'link_count': link_count, 'new_layers': new_layers }

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
      QgsMessageLog.logMessage("Result: {}".format(result), 'Harmony Plugin')
      iface = result['iface']
      status = result['status']
      link_count = result['link_count']
      new_layers = result['new_layers']
      new_iface_layers = []
      for layerName, fileName in new_layers:
        layer = iface.addRasterLayer(fileName, layerName)
        if not layer or not layer.isValid():
          QgsMessageLog.logMessage("Failed to create layer {}".format(layerName), 'Harmony Plugin')

      if status != 'done':
        QgsMessageLog.logMessage('Starting next worker', 'Harmony Plugin')
        response = result['response']
        task = QgsTask.fromFunction('Worker', pollResults, on_finished=completed, iface=iface, response=response, link_count=link_count)
        globals()['task'] = task
        QgsApplication.taskManager().addTask(globals()['task'])
      else:
        QgsMessageLog.logMessage('Completed with no errors')
  else:
    QgsMessageLog.logMessage("Exception: {}".format(exception), 'Harmony Plugin')
    raise exception

def handleAsyncResponse(iface, response):
  QgsMessageLog.logMessage('Async request started', 'Harmony Plugin')
  task = QgsTask.fromFunction('Worker', pollResults, on_finished=completed, iface=iface, response=response, link_count=0)
  globals()['task'] = task
  QgsApplication.taskManager().addTask(globals()['task'])
  QgsMessageLog.logMessage('Workers started', 'Harmony Plugin')

def handleSyncResponse(iface, response, layerName, variable):
  with open(tempfile.gettempdir() + os.path.sep + 'harmony_output_image.tif', 'wb') as fd:
    for chunk in response.iter_content(chunk_size=128):
      fd.write(chunk)

  iface.addRasterLayer(tempfile.gettempdir() + os.path.sep + 'harmony_output_image.tif', layerName + '-' + variable)

def handleHarmonyResponse(iface, response, layerName, variable):
  content_type = response.headers['Content-Type']
  message = 'Content-type is: ' + content_type
  QgsMessageLog.logMessage(message, 'Harmony Plugin')

  if content_type == 'application/json; charset=utf-8':
    handleAsyncResponse(iface, response)
  else:
    handleSyncResponse(iface, response, layerName, variable)
