from datetime import datetime
from time import sleep
import json

import http.client as http_client
import logging

import tempfile
import os
import requests

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
  return [link['href'] for link in response.json()['links'] if link.get('rel', 'data') == 'data']


def show(iface, response, layerName, variable):
  tmp = tempfile.NamedTemporaryFile(suffix='.tif', delete=False)
  try:
    tmp.write(response.content)
    iface.addRasterLayer(tmp.name, layerName + '-' + variable)
  finally:
    os.unlink(tmp.name)

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
    print('Async response at', datetime.now().strftime("%H:%M:%S"))
    print(json.dumps(response.json(), indent=2))
    links = get_data_urls(response)
    new_links = links[slice(link_count, None)]
    for link in new_links:
      if link.startswith('http'):
        show(iface, get(link), 'layer', link_count)
    return len(links)

  displayed_link_count = 0
  body = response.json()
  displayed_link_count = show_response(iface, response, displayed_link_count)
  waiting_message_printed = False
  while body['status'] not in ['successful', 'failed']:
    if not waiting_message_printed:
      print('Waiting for updates...')
      waiting_message_printed = True
    sleep(1)
    progress = body['progress']
    status = body['status']
    response = session.get(response.url)
    body = response.json()
    if progress != body['progress'] or status != body['status']:
      displayed_link_count = show_response(iface, response, displayed_link_count)
      waiting_message_printed = False
  print('Async request is complete')
  return response

def handleAsyncResponse(iface, response):
  show_async(iface, response)

def handleSyncResponse(iface, response, layerName, variable):
  with open('/tmp/harmony_output_image.tif', 'wb') as fd:
    for chunk in response.iter_content(chunk_size=128):
      fd.write(chunk)

  iface.addRasterLayer('/tmp/harmony_output_image.tif', layerName + '-' + variable)

def handleHarmonyResponse(iface, response, layerName, variable):
  content_type = response.headers['Content-Type']
  if content_type == 'application/json':
    handleAsyncResponse(iface, response)
  else:
    handleSyncResponse(iface, response, layerName, variable)
