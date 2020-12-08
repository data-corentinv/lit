"""Notebook usage of LIT."""

import html
import json
import os
import pathlib
import random
import typing
from absl import flags
# pytype: disable=import-error
from IPython import display
from lit_nlp import dev_server
from lit_nlp import server_flags
from lit_nlp.lib import wsgi_serving

try:
  import google.colab  # pylint: disable=g-import-not-at-top,unused-import
  is_colab = True
except ImportError:
  is_colab = False

flags.FLAGS.set_default('server_type', 'notebook')
flags.FLAGS.set_default('host', 'localhost')
flags.FLAGS.set_default('port', None)


def start_lit(models, datasets, height=1000, proxy_url=None):
  """Start and display a LIT instance in a notebook instance.

  Args:
    models: A dict of model names to LIT model instances.
    datasets: A dict of dataset names to LIT dataset instances.
    height: Height to display the LIT UI in pixels. Defaults to 1000.
    proxy_url: Optional proxy URL, if using in a notebook with a server proxy.
        Defaults to None.

  Returns:
    Callback method to stop the LIT server.

  """
  lit_demo = dev_server.Server(models, datasets, **server_flags.get_flags())
  server = typing.cast(wsgi_serving.NotebookWsgiServer, lit_demo.serve())

  if is_colab:
    _display_colab(server.port, height)
  else:
    _display_jupyter(server.port, height, proxy_url)

  return server.stop


def _display_colab(port, height):
  """Display the LIT UI in colab.

  Args:
    port: The port the LIT server is running on.
    height: The height of the LIT UI in pixels.
  """

  shell = """
      (async () => {
          const url = new URL(
            await google.colab.kernel.proxyPort(%PORT%, {'cache': true}));
          const iframe = document.createElement('iframe');
          iframe.src = url;
          iframe.setAttribute('width', '100%');
          iframe.setAttribute('height', '%HEIGHT%px');
          iframe.setAttribute('frameborder', 0);
          document.body.appendChild(iframe);
      })();
  """
  replacements = [
      ('%PORT%', '%d' % port),
      ('%HEIGHT%', '%d' % height),
  ]
  for (k, v) in replacements:
    shell = shell.replace(k, v)

  script = display.Javascript(shell)
  display.display(script)


def _display_jupyter(port, height, proxy_url):
  """Display the LIT UI in colab.

  Args:
    port: The port the LIT server is running on.
    height: The height of the LIT UI in pixels.
    proxy_url: Optional proxy URL, if using in a notebook with a server proxy.
  """

  frame_id = 'lit-frame-{:08x}'.format(random.getrandbits(64))
  shell = """
    <iframe id='%HTML_ID%' width='100%' height='%HEIGHT%' frameborder='0'>
    </iframe>
    <script>
      (function() {
        const frame = document.getElementById(%JSON_ID%);
        const url = new URL(%URL%, window.location);
        const port = %PORT%;
        if (port) {
          url.port = port;
        }
        frame.src = url;
      })();
    </script>
  """
  if proxy_url is not None:
    # Allow %PORT% in proxy_url.
    proxy_url = proxy_url.replace('%PORT%', '%d' % port)
    replacements = [
        ('%HTML_ID%', html.escape(frame_id, quote=True)),
        ('%JSON_ID%', json.dumps(frame_id)),
        ('%HEIGHT%', '%d' % height),
        ('%PORT%', '0'),
        ('%URL%', json.dumps(proxy_url)),
    ]
  else:
    replacements = [
        ('%HTML_ID%', html.escape(frame_id, quote=True)),
        ('%JSON_ID%', json.dumps(frame_id)),
        ('%HEIGHT%', '%d' % height),
        ('%PORT%', '%d' % port),
        ('%URL%', json.dumps('/')),
    ]

  for (k, v) in replacements:
    shell = shell.replace(k, v)

  iframe = display.HTML(shell)
  display.display(iframe)
