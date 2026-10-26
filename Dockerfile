FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 GOTOOLCHAIN=local
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv python3-pip golang-go nginx protobuf-compiler golang-cfssl ca-certificates openssl curl iproute2 git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:/root/go/bin:${PATH}"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN go install google.golang.org/protobuf/cmd/protoc-gen-go@v1.36.5 && go install google.golang.org/grpc/cmd/protoc-gen-go-grpc@v1.5.1
COPY . .
RUN sh scripts/generate.sh && mkdir -p bin artifacts && go build -o bin/dice-server ./server && go test ./... && python manage.py check && python manage.py test client -v 2
EXPOSE 8000 8001
CMD ["python", "scripts/start.py"]
