#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python -m grpc_tools.protoc -I proto --python_out=client/api --grpc_python_out=client/api proto/api.proto
python - <<'FIX'
from pathlib import Path
p=Path("client/api/api_pb2_grpc.py")
p.write_text(p.read_text().replace("import api_pb2 as api__pb2", "from . import api_pb2 as api__pb2"))
FIX
protoc -I proto --go_out=. --go_opt=module=python_go_grpc --go-grpc_out=. --go-grpc_opt=module=python_go_grpc proto/api.proto
gofmt -w server
go mod tidy
