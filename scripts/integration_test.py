"""Real network tests: run inside the started Ubuntu container."""
import concurrent.futures
import http.cookiejar
import json
from pathlib import Path
import ssl
import sys
import time
import unittest
import urllib.parse
import urllib.request
import grpc

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from client.api import api_pb2, api_pb2_grpc
from client.api.client import Client, Certs

ROOT = Path(__file__).resolve().parent.parent
CERTS = Certs.load(ROOT / 'certs')
SAMPLES = {}

def json_get(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.load(response)

def post_roll(port):
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    url = f'http://127.0.0.1:{port}/'
    opener.open(url, timeout=10).read()
    import re
    html = opener.open(url, timeout=10).read().decode()
    token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)
    data = urllib.parse.urlencode({'csrfmiddlewaretoken': token}).encode()
    with opener.open(urllib.request.Request(url, data, headers={'Referer': url}), timeout=15) as response:
        text = response.read().decode()
        assert response.status == 200 and text.count('Значение:') == 2, text
        return {'port': port, 'status': response.status, 'both_dice_rendered': True}

class NetworkTests(unittest.TestCase):
    def test_01_direct_mtls(self):
        values = [Client('127.0.0.1:8443', CERTS).roll_die() for _ in range(30)]
        self.assertTrue(all(1 <= value <= 6 for value in values))
        SAMPLES['direct'] = values

    def test_02_nginx_mtls(self):
        values = [Client('127.0.0.1:9448', CERTS).roll_die() for _ in range(30)]
        self.assertTrue(all(1 <= value <= 6 for value in values))
        SAMPLES['nginx'] = values

    def test_03_missing_client_certificate_is_rejected(self):
        for address in ['127.0.0.1:8443', '127.0.0.1:9448']:
            credentials = grpc.ssl_channel_credentials(root_certificates=CERTS.root)
            with grpc.secure_channel(address, credentials) as channel:
                with self.assertRaises(grpc.RpcError):
                    api_pb2_grpc.DiceServiceStub(channel).RollDie(api_pb2.RollDieRequest(), timeout=2)

    def test_04_wrong_certificate_purpose_is_rejected(self):
        # A server certificate must not authenticate a client.
        wrong = Certs(CERTS.root, (ROOT/'certs/server.pem').read_bytes(), (ROOT/'certs/server-key.pem').read_bytes())
        for address in ['127.0.0.1:8443', '127.0.0.1:9448']:
            with self.assertRaises(grpc.RpcError):
                Client(address, wrong).roll_die()

    def test_05_two_clients_and_json_endpoints(self):
        for port in [8000, 8001]:
            self.assertEqual(json_get(f'http://127.0.0.1:{port}/health')['status'], 'ok')
            for path in ['grpc', 'nginx']:
                value = json_get(f'http://127.0.0.1:{port}/{path}')['value']
                self.assertIn(value, range(1, 7))

    def test_06_concurrent_browser_forms(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(post_roll, [8000, 8001, 8000, 8001]))
        SAMPLES['forms'] = results

    def test_07_nginx_status_requires_mtls(self):
        context = ssl.create_default_context(cafile=str(ROOT/'certs/ca.pem'))
        context.load_cert_chain(str(ROOT/'certs/client.pem'), str(ROOT/'certs/client-key.pem'))
        with urllib.request.urlopen('https://127.0.0.1:9448/nginx_status', context=context, timeout=5) as response:
            self.assertIn('Active connections', response.read().decode())

if __name__ == '__main__':
    started = time.time()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NetworkTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    payload = {'tests_run': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors), 'passed': result.wasSuccessful(), 'duration_seconds': round(time.time()-started, 2), 'samples': SAMPLES}
    (ROOT/'artifacts/integration.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False)+'\n')
    sys.exit(0 if result.wasSuccessful() else 1)
