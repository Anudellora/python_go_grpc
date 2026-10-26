#!/bin/sh
# Run on Ubuntu 24.04 from the project root.
set -eu
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip golang-go nginx protobuf-compiler golang-cfssl ca-certificates openssl curl iproute2 git
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
export PATH="$PATH:$(go env GOPATH)/bin"
go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.36.5
go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.5.1
sh scripts/generate.sh
sh certs.sh
mkdir -p bin artifacts
go build -o bin/dice-server ./server
python manage.py check
