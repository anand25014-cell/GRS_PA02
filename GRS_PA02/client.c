#include "common.h"
#include <time.h>
#include <sys/time.h>

#define SEND_BUF_SIZE 1024   // bytes per send()

struct thread_args {
    char ip[32];
    int port;
    int duration;
    long long bytes_sent;
};

/* Sender thread */
void *sender(void *arg) {
    struct thread_args *ta = arg;

    int fd = socket(AF_INET, SOCK_STREAM, 0);

    struct sockaddr_in srv = {0};
    srv.sin_family = AF_INET;
    srv.sin_port = htons(ta->port);
    inet_pton(AF_INET, ta->ip, &srv.sin_addr);

    connect(fd, (struct sockaddr*)&srv, sizeof(srv));

    /* ---- IMPORTANT FIX: send timeout ---- */
    struct timeval snd_timeout;
    snd_timeout.tv_sec = 1;    // max 1s blocking
    snd_timeout.tv_usec = 0;
    setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO,
               &snd_timeout, sizeof(snd_timeout));
    /* ------------------------------------- */

    char buf[SEND_BUF_SIZE];
    memset(buf, 'X', sizeof(buf));

    struct timeval start, now;
    gettimeofday(&start, NULL);

    ta->bytes_sent = 0;

    while (1) {
        gettimeofday(&now, NULL);

        double elapsed =
            (now.tv_sec - start.tv_sec) +
            (now.tv_usec - start.tv_usec) / 1e6;

        if (elapsed >= ta->duration)
            break;

        /* ---- NON-BLOCKING SAFE SEND ---- */
        ssize_t s = send(fd, buf, sizeof(buf), 0);
        if (s > 0)
            ta->bytes_sent += s;
        /* -------------------------------- */
    }

    close(fd);
    return NULL;
}

int main(int argc, char **argv) {
    if (argc < 5) {
        printf("Usage: %s <server_ip> <port> <threads> <duration>\n", argv[0]);
        exit(1);
    }

    int threads = atoi(argv[3]);
    int duration = atoi(argv[4]);

    pthread_t tids[threads];
    struct thread_args *args[threads];

    struct timeval start, end;
    gettimeofday(&start, NULL);

    /* Create threads */
    for (int i = 0; i < threads; i++) {
        args[i] = malloc(sizeof(struct thread_args));
        strcpy(args[i]->ip, argv[1]);
        args[i]->port = atoi(argv[2]);
        args[i]->duration = duration;
        args[i]->bytes_sent = 0;

        pthread_create(&tids[i], NULL, sender, args[i]);
    }

    /* Join threads */
    long long total_bytes = 0;
    for (int i = 0; i < threads; i++) {
        pthread_join(tids[i], NULL);
        total_bytes += args[i]->bytes_sent;
        free(args[i]);
    }

    gettimeofday(&end, NULL);

    double total_time =
        (end.tv_sec - start.tv_sec) +
        (end.tv_usec - start.tv_usec) / 1e6;

    double throughput_mbps =
        (total_bytes * 8.0) / (total_time * 1e6);

    double latency_us =
        (total_time * 1e6) / (total_bytes / SEND_BUF_SIZE);

    printf("\n===== CLIENT RESULTS =====\n");
    printf("Threads            : %d\n", threads);
    printf("Duration (s)        : %d\n", duration);
    printf("Total bytes sent    : %lld\n", total_bytes);
    printf("Throughput (Mbps)   : %.2f\n", throughput_mbps);
    printf("Avg latency (us)    : %.2f\n", latency_us);
    printf("==========================\n");

    return 0;
}
