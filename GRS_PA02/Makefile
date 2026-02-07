##MT25014

CC = gcc
CFLAGS = -Wall -pthread -O2
TARGETS = server client

all: $(TARGETS)

server: server.c common.h
	$(CC) $(CFLAGS) -o server server.c

client: client.c common.h
	$(CC) $(CFLAGS) -o client client.c

clean:
	rm -f $(TARGETS) *.o perf_*.txt bytes_*.tmp *.csv *.txt *.png

.PHONY: all clean