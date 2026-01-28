#include "common.h"
#include <time.h>
#include <linux/errqueue.h>
#include <netinet/ip.h>

#define SERVER_RUN_TIME 10   // seconds per client

struct message {
    char *fields[NUM_FIELDS];
    size_t sizes[NUM_FIELDS];
};

struct client_args {
    int fd;
    size_t msg_size;
    char mode[16];   // twocopy | onecopy | zerocopy
};

/* Allocate message with 8 heap-allocated fields */
struct message *create_message(size_t total) {
    struct message *m = malloc(sizeof(*m));
    size_t per = total / NUM_FIELDS;

    for (int i = 0; i < NUM_FIELDS; i++) {
        m->sizes[i] = per;
        m->fields[i] = malloc(per);
        memset(m->fields[i], 'A' + i, per);
    }
    return m;
}

void free_message(struct message *m) {
    for (int i = 0; i < NUM_FIELDS; i++)
        free(m->fields[i]);
    free(m);
}

/* ===================================================== */
/* *** ZERO-COPY COMPLETION HANDLER (REQUIRED) *** */
static void wait_for_zerocopy_completion(int fd) {
    char ctrl[CMSG_SPACE(sizeof(struct sock_extended_err))];
    char data[1];

    struct iovec iov = {
        .iov_base = data,
        .iov_len  = sizeof(data),
    };

    struct msghdr msg = {
        .msg_iov = &iov,
        .msg_iovlen = 1,
        .msg_control = ctrl,
        .msg_controllen = sizeof(ctrl),
    };

    while (1) {
        ssize_t ret = recvmsg(fd, &msg, MSG_ERRQUEUE);
        if (ret < 0) {
            if (errno == EAGAIN || errno == EWOULDBLOCK)
                break;
            perror("recvmsg MSG_ERRQUEUE");
            break;
        }

        for (struct cmsghdr *cmsg = CMSG_FIRSTHDR(&msg);
             cmsg != NULL;
             cmsg = CMSG_NXTHDR(&msg, cmsg)) {

            if (cmsg->cmsg_level == SOL_IP &&
                cmsg->cmsg_type == IP_RECVERR) {

                struct sock_extended_err *err =
                    (struct sock_extended_err *)CMSG_DATA(cmsg);

                if (err->ee_origin == SO_EE_ORIGIN_ZEROCOPY) {
                    return;   // completion received
                }
            }
        }
    }
}
/* ===================================================== */

/* Per-client thread */
void *client_thread(void *arg) {
    struct client_args *ca = arg;
    struct message *msg = create_message(ca->msg_size);

    struct iovec iov[NUM_FIELDS];
    for (int i = 0; i < NUM_FIELDS; i++) {
        iov[i].iov_base = msg->fields[i];
        iov[i].iov_len  = msg->sizes[i];
    }

    struct msghdr mh;
    memset(&mh, 0, sizeof(mh));
    mh.msg_iov = iov;
    mh.msg_iovlen = NUM_FIELDS;

    char recv_buf[4096];
    time_t start = time(NULL);

    while (time(NULL) - start < SERVER_RUN_TIME) {

        /* Drain client data */
        ssize_t r = recv(ca->fd, recv_buf, sizeof(recv_buf), MSG_DONTWAIT);
        if (r == 0)
            break;

        if (strcmp(ca->mode, "twocopy") == 0) {

            size_t total = ca->msg_size;
            char *tmp = malloc(total);
            size_t off = 0;

            for (int i = 0; i < NUM_FIELDS; i++) {
                memcpy(tmp + off, msg->fields[i], msg->sizes[i]);
                off += msg->sizes[i];
            }

            send(ca->fd, tmp, total, 0);
            free(tmp);

        } else if (strcmp(ca->mode, "onecopy") == 0) {

            sendmsg(ca->fd, &mh, 0);

        } else if (strcmp(ca->mode, "zerocopy") == 0) {

#ifdef MSG_ZEROCOPY
            sendmsg(ca->fd, &mh, MSG_ZEROCOPY);

            /* *** REQUIRED: wait before reusing buffers *** */
            wait_for_zerocopy_completion(ca->fd);
#else
            sendmsg(ca->fd, &mh, 0);
#endif
        }
    }

    free_message(msg);
    close(ca->fd);
    free(ca);
    return NULL;
}

int main(int argc, char **argv) {
    if (argc < 3) {
        printf("Usage: %s <twocopy|onecopy|zerocopy> <msg_size>\n", argv[0]);
        exit(1);
    }

    int server_fd = socket(AF_INET, SOCK_STREAM, 0);

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in addr = {0};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(DEFAULT_PORT);
    addr.sin_addr.s_addr = INADDR_ANY;

    bind(server_fd, (struct sockaddr*)&addr, sizeof(addr));
    listen(server_fd, BACKLOG);

    printf("Server listening on port %d (mode=%s, msg_size=%s)\n",
           DEFAULT_PORT, argv[1], argv[2]);

    while (1) {
        int client_fd = accept(server_fd, NULL, NULL);

        struct client_args *ca = malloc(sizeof(*ca));
        ca->fd = client_fd;
        ca->msg_size = atoi(argv[2]);
        strcpy(ca->mode, argv[1]);

        pthread_t tid;
        pthread_create(&tid, NULL, client_thread, ca);
        pthread_detach(tid);
    }

    close(server_fd);
    return 0;
}
