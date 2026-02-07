# MT25014 PA02 Makefile

CC = gcc
CFLAGS = -Wall -pthread -O2

SERVER_SRC = MT25014_Part_A_Server.c
CLIENT_SRC = MT25014_Part_A_Client.c
COMMON_HDR = MT25014_Part_A_Common.h

TARGETS = server client

all: $(TARGETS)

server: $(SERVER_SRC) $(COMMON_HDR)
	$(CC) $(CFLAGS) -o server $(SERVER_SRC)

client: $(CLIENT_SRC) $(COMMON_HDR)
	$(CC) $(CFLAGS) -o client $(CLIENT_SRC)

clean:
	rm -f $(TARGETS) *.o perf_*.txt bytes_*.tmp *.csv *.txt *.png

.PHONY: all clean
