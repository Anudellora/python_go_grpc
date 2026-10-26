package main

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
	"google.golang.org/grpc/peer"
	"google.golang.org/grpc/status"
	"log"
	"net"
	"os"
	"os/signal"
	"python_go_grpc/server/api"
	"syscall"
	"time"
)

func loggingInterceptor(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
	start := time.Now()
	result, err := handler(ctx, req)
	addr := "unknown"
	if p, ok := peer.FromContext(ctx); ok {
		addr = p.Addr.String()
	}
	log.Printf("peer=%s method=%s status=%s duration=%s", addr, info.FullMethod, status.Code(err), time.Since(start))
	return result, err
}
func main() {
	pair, err := tls.LoadX509KeyPair("certs/server.pem", "certs/server-key.pem")
	if err != nil {
		log.Fatal(err)
	}
	ca, err := os.ReadFile("certs/ca.pem")
	if err != nil {
		log.Fatal(err)
	}
	pool := x509.NewCertPool()
	if !pool.AppendCertsFromPEM(ca) {
		log.Fatal("invalid CA")
	}
	config := &tls.Config{Certificates: []tls.Certificate{pair}, ClientCAs: pool, ClientAuth: tls.RequireAndVerifyClientCert, MinVersion: tls.VersionTLS12}
	secure := grpc.NewServer(grpc.Creds(credentials.NewTLS(config)), grpc.UnaryInterceptor(loggingInterceptor))
	plain := grpc.NewServer(grpc.UnaryInterceptor(loggingInterceptor))
	api.RegisterDiceServiceServer(secure, api.NewServer())
	api.RegisterDiceServiceServer(plain, api.NewServer())
	servers := []*grpc.Server{secure, plain}
	addresses := []string{"127.0.0.1:8443", "127.0.0.1:50051"}
	errors := make(chan error, 2)
	for i, srv := range servers {
		listener, err := net.Listen("tcp", addresses[i])
		if err != nil {
			log.Fatal(err)
		}
		log.Printf("Starting gRPC address=%s mtls=%t", addresses[i], i == 0)
		go func(s *grpc.Server, l net.Listener) { errors <- s.Serve(l) }(srv, listener)
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	select {
	case <-ctx.Done():
		log.Print("Shutdown requested")
	case err := <-errors:
		log.Print(fmt.Errorf("gRPC stopped: %w", err))
	}
	done := make(chan struct{})
	go func() {
		for _, s := range servers {
			s.GracefulStop()
		}
		close(done)
	}()
	select {
	case <-done:
	case <-time.After(5 * time.Second):
		for _, s := range servers {
			s.Stop()
		}
	}
}
