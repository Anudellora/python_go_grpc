package api

import (
	"context"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/status"
	"testing"
)

func TestRollDieRange(t *testing.T) {
	s := NewServer()
	for i := 0; i < 1000; i++ {
		got, err := s.RollDie(context.Background(), &RollDieRequest{})
		if err != nil || got.Value < 1 || got.Value > 6 {
			t.Fatalf("invalid result: %v %v", got, err)
		}
	}
}
func TestCancelledRequest(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	_, err := NewServer().RollDie(ctx, &RollDieRequest{})
	if status.Code(err) != codes.Canceled {
		t.Fatalf("expected Canceled: %v", err)
	}
}
