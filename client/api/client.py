from dataclasses import dataclass
from pathlib import Path
import grpc
from . import api_pb2, api_pb2_grpc

@dataclass(frozen=True)
class Certs:
    root: bytes
    cert: bytes
    key: bytes

    @classmethod
    def load(cls, directory):
        directory = Path(directory)
        return cls(*( (directory / name).read_bytes() for name in ("ca.pem", "client.pem", "client-key.pem") ))

class Client:
    def __init__(self, addr, certs):
        self.addr, self.certs = addr, certs

    def roll_die(self):
        credentials = grpc.ssl_channel_credentials(root_certificates=self.certs.root, private_key=self.certs.key, certificate_chain=self.certs.cert)
        with grpc.secure_channel(self.addr, credentials) as channel:
            value = api_pb2_grpc.DiceServiceStub(channel).RollDie(api_pb2.RollDieRequest(), timeout=5).value
        if not 1 <= value <= 6:
            raise ValueError(f"Invalid die result: {value}")
        return value
