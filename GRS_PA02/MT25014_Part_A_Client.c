#include "common.h"

void *receive_data(void *args) {
    thread_args_t *t_args = (thread_args_t *)args;
    char *buf = malloc(t_args->msg_size);
    long local_bytes = 0;
    long local_msg_count = 0;
    double local_latency_sum = 0.0;
    
    struct timeval start, now, msg_start, msg_end;
    gettimeofday(&start, NULL);

    while (1) {
        gettimeofday(&now, NULL);
        double elapsed = (now.tv_sec - start.tv_sec) + (now.tv_usec - start.tv_usec) / 1000000.0;
        if (elapsed >= t_args->duration) break;

        // Measure per-message latency
        gettimeofday(&msg_start, NULL);
        ssize_t received = recv(t_args->fd, buf, t_args->msg_size, 0);
        gettimeofday(&msg_end, NULL);
        
        if (received > 0) {
            local_bytes += received;
            local_msg_count++;
            
            // Calculate latency in microseconds
            double lat_us = (msg_end.tv_sec - msg_start.tv_sec) * 1000000.0 +
                           (msg_end.tv_usec - msg_start.tv_usec);
            local_latency_sum += lat_us;
        } else if (received == 0) {
            break; // Connection closed
        } else if (errno != EAGAIN && errno != EWOULDBLOCK) {
            break; // Error
        }
    }

    // Update global counters safely
    pthread_mutex_lock(t_args->mutex);
    *(t_args->bytes_counter) += local_bytes;
    *(t_args->msg_count) += local_msg_count;
    *(t_args->latency_sum) += local_latency_sum;
    pthread_mutex_unlock(t_args->mutex);

    free(buf);
    close(t_args->fd);
    free(t_args);
    return NULL;
}

int main(int argc, char *argv[]) {
    if (argc < 5) {
        fprintf(stderr, "Usage: %s <server_ip> <msg_size> <num_threads> <duration>\n", argv[0]);
        return 1;
    }
    
    char *server_ip = argv[1];
    int msg_size = atoi(argv[2]);
    int num_threads = atoi(argv[3]);
    int duration = atoi(argv[4]);

    long total_bytes = 0;
    long total_messages = 0;
    double total_latency_us = 0.0;
    pthread_mutex_t counter_mutex = PTHREAD_MUTEX_INITIALIZER;
    pthread_t threads[num_threads];

    for (int i = 0; i < num_threads; i++) {
        int sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) {
            perror("socket");
            continue;
        }
        
        struct sockaddr_in addr = {0};
        addr.sin_family = AF_INET;
        addr.sin_port = htons(PORT);
        inet_pton(AF_INET, server_ip, &addr.sin_addr);
        
        if (connect(sock, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
            perror("connect");
            close(sock);
            continue;
        }

        thread_args_t *t_args = malloc(sizeof(thread_args_t));
        t_args->fd = sock;
        t_args->msg_size = msg_size;
        t_args->duration = duration;
        t_args->bytes_counter = &total_bytes;
        t_args->msg_count = &total_messages;
        t_args->latency_sum = &total_latency_us;
        t_args->mutex = &counter_mutex;
        
        pthread_create(&threads[i], NULL, receive_data, t_args);
    }

    for (int i = 0; i < num_threads; i++) {
        pthread_join(threads[i], NULL);
    }

    // Calculate average latency
    double avg_latency_us = (total_messages > 0) ? (total_latency_us / total_messages) : 0.0;
    
    // Output format: bytes,avg_latency_us
    // This will be parsed by the bash script
    printf("%ld,%.2f\n", total_bytes, avg_latency_us);
    
    return 0;
}


