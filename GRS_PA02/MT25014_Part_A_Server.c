#include "common.h"

void *handle_client(void *args) {
    thread_args_t *t_args = (thread_args_t *)args;
    int fd = t_args->fd;
    int field_size = t_args->msg_size / NUM_FIELDS;
    
    // Allocate 8 fields on heap
    Message msg;
    for(int i=0; i<NUM_FIELDS; i++) {
        msg.fields[i] = malloc(field_size);
        memset(msg.fields[i], 'A' + i, field_size);
    }

    if (t_args->mode == 2) {
        int one = 1;
        if (setsockopt(fd, SOL_SOCKET, SO_ZEROCOPY, &one, sizeof(one))) {
            perror("setsockopt zerocopy");
        }
    }

    struct timeval start, now;
    gettimeofday(&start, NULL);

    while (1) {
        gettimeofday(&now, NULL);
        double elapsed = (now.tv_sec - start.tv_sec) + (now.tv_usec - start.tv_usec) / 1000000.0;
        if (elapsed >= t_args->duration) break;
        if (t_args->mode == 0) {
            // A1: Two-Copy (Manual pack into single buffer + send)
            char *flat_buf = malloc(t_args->msg_size);
            for(int i=0; i<NUM_FIELDS; i++)
                memcpy(flat_buf + (i*field_size), msg.fields[i], field_size);
            send(fd, flat_buf, t_args->msg_size, 0);
            free(flat_buf);
        } 
        else if (t_args->mode == 1 || t_args->mode == 2) {
            // A2 & A3: Scatter-Gather using iovec
            struct iovec iov[NUM_FIELDS];
            struct msghdr msgh = {0};
            for(int i=0; i<NUM_FIELDS; i++) {
                iov[i].iov_base = msg.fields[i];
                iov[i].iov_len = field_size;
            }
            msgh.msg_iov = iov;
            msgh.msg_iovlen = NUM_FIELDS;
            
            int flags = (t_args->mode == 2) ? MSG_ZEROCOPY : 0;
            if (sendmsg(fd, &msgh, flags) < 0) {
                if (errno != ENOBUFS) perror("sendmsg failed");
            }
        }
    }

    for(int i=0; i<NUM_FIELDS; i++) free(msg.fields[i]);
    close(fd);
    free(t_args);
    return NULL;
}

int main(int argc, char *argv[]) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <mode> <msg_size> <duration>\n", argv[0]);
        return 1;
    }

    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(PORT);
    addr.sin_addr.s_addr = INADDR_ANY;
    
    bind(server_fd, (struct sockaddr *)&addr, sizeof(addr));
    listen(server_fd, 64);

    while (1) {
        struct sockaddr_in client_addr;
        socklen_t len = sizeof(client_addr);
        int client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &len);
        
        thread_args_t *args = malloc(sizeof(thread_args_t));
        args->fd = client_fd;
        args->mode = atoi(argv[1]);
        args->msg_size = atoi(argv[2]);
        args->duration = atoi(argv[3]);

        pthread_t tid;
        pthread_create(&tid, NULL, handle_client, args);
        pthread_detach(tid);
    }
    return 0;
}