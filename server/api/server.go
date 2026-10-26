package api

import (
	"context"
	"crypto/rand"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"math/big"
)

type Server struct{ UnimplementedDiceServiceServer }

func NewServer() *Server { return &Server{} }
func (s *Server) RollDie(ctx context.Context, req *RollDieRequest) (*RollDieResponse, error) {
	if err := ctx.Err(); err != nil {
		return nil, status.FromContextError(err).Err()
	}
	n, err := rand.Int(rand.Reader, big.NewInt(6))
	if err != nil {
		return nil, status.Error(codes.Internal, "random number generation failed")
	}
	return &RollDieResponse{Value: int32(n.Int64() + 1)}, nil
}
