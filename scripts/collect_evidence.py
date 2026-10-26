"""Capture real commands and their outputs for the practical report."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent.parent

def run(command):
    result = subprocess.run(command, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return {'command': ' '.join(command), 'exit_code': result.returncode, 'output': result.stdout.strip()}

groups = {
    'environment': [
        ['cat', '/etc/os-release'], ['go', 'version'], ['python', '--version'], ['python', '-m', 'django', '--version'], ['python', '-c', 'import grpc; print("grpcio", grpc.__version__)'], ['nginx', '-v'], ['protoc', '--version'], ['cfssl', 'version'],
    ],
    'certificates': [
        ['openssl', 'verify', '-CAfile', 'certs/ca.pem', '-purpose', 'sslserver', 'certs/server.pem'],
        ['openssl', 'verify', '-CAfile', 'certs/ca.pem', '-purpose', 'sslclient', 'certs/client.pem'],
        ['openssl', 'x509', '-in', 'certs/server.pem', '-noout', '-subject', '-issuer', '-dates', '-ext', 'subjectAltName'],
        ['openssl', 'x509', '-in', 'certs/client.pem', '-noout', '-ext', 'extendedKeyUsage'],
    ],
    'generation': [
        ['cat', 'proto/api.proto'],
        ['find', 'client/api', 'server/api', '-maxdepth', '1', '-type', 'f'],
        ['python', '-c', 'from client.api import api_pb2, api_pb2_grpc; print("Python protobuf imports: OK"); print("RPC:", api_pb2.DESCRIPTOR.services_by_name["DiceService"].methods[0].full_name)'],
    ],
    'services': [
        ['nginx', '-t', '-p', str(root)+'/', '-c', 'nginx.conf'],
        ['ss', '-lnt'], ['curl', '-fsS', 'http://127.0.0.1:8000/health'], ['curl', '-fsS', 'http://127.0.0.1:8001/health'],
    ],
    'tests': [
        ['python', 'manage.py', 'check'], ['go', 'test', './...', '-v'], ['python', 'manage.py', 'test', 'client', '-v', '2'], ['python', 'scripts/integration_test.py'],
    ],
}
payload = {'captured_at': datetime.now(timezone.utc).isoformat(), 'groups': {name: [run(command) for command in commands] for name, commands in groups.items()}}
(root/'artifacts/evidence.json').write_text(json.dumps(payload, indent=2, ensure_ascii=False)+'\n')
lock = run(['pip','freeze'])
(root/'artifacts/python-lock.txt').write_text(lock['output']+'\n')
for group,commands in payload['groups'].items():
    print('\n=== '+group+' ===')
    for item in commands:
        print('$ '+item['command']+'\n'+item['output']+'\nexit_code='+str(item['exit_code']))
raise SystemExit(0 if all(c['exit_code']==0 for cmds in payload['groups'].values() for c in cmds) else 1)
