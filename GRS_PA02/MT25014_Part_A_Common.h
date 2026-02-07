#ifndef COMMON_H
#define COMMON_H

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <sys/time.h>
#include <errno.h>
#include <sys/uio.h>
#include <linux/errqueue.h>

#define NUM_FIELDS 8
#define PORT 8080
#define DEFAULT_PORT 8080


typedef struct {
    char *fields[NUM_FIELDS];
} Message;

typedef struct {
    int fd;
    int mode;
    int msg_size;
    int duration;
    long *bytes_counter;
    double *latency_sum;      // NEW: For latency tracking
    long *msg_count;          // NEW: For message count
    pthread_mutex_t *mutex;
} thread_args_t;

#ifndef SO_ZEROCOPY
#define SO_ZEROCOPY 60
#endif

#ifndef MSG_ZEROCOPY
#define MSG_ZEROCOPY 0x4000000
#endif

#endif