import subprocess
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import threading
import logging

TOKEN = os.environ.get('WEBHOOK_TOKEN', 'sat-deploy-9x7k2m')
PORT = 9000

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger('webhook')

class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        query = self.path.split('?')[-1] if '?' in self.path else ''
        params = dict(q.split('=') for q in query.split('&') if '=' in q)

        if self.path.startswith('/webhook') and params.get('token') == TOKEN:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            try:
                data = json.loads(body)
                event = self.headers.get('X-GitHub-Event', '')
                if event == 'push' and data.get('ref', '').endswith('main'):
                    logger.info('Push a main detectado. Deploy iniciado.')
                    threading.Thread(target=self.run_deploy, daemon=True).start()
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'Deploy iniciado')
                else:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'Evento ignorado')
            except Exception as e:
                logger.error(f'Error: {e}')
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b'Forbidden')

    def run_deploy(self):
        try:
            result = subprocess.run(['/home/ubuntu/Saturday/deploy.sh'], timeout=300, capture_output=True, text=True)
            logger.info(f'Deploy stdout: {result.stdout}')
            if result.stderr:
                logger.error(f'Deploy stderr: {result.stderr}')
        except Exception as e:
            logger.error(f'Deploy failed: {e}')

    def log_message(self, format, *args):
        logger.info(f'{args[0]}')

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', PORT), WebhookHandler)
    logger.info(f'Webhook server escuchando en puerto {PORT}')
    server.serve_forever()
