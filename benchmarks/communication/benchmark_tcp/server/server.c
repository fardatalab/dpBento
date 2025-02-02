#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <unistd.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <string.h>
#include <fcntl.h>
#include <time.h>
#include <pthread.h>
#include <sys/times.h>
#include <sys/time.h>

#define PAGE_SIZE 4096 // 4 kB
#define MAX_FILE_SIZE 1048576 // Maximum file size is 1024kB

struct thread_args {
    int client_sock;
    int total_requests;
};

void *handle_client(void *args);

int listen_to_client(int port){
    int server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        fprintf(stderr, "Error creating socket\n");
        return -1;
    }
    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    addr.sin_addr.s_addr = INADDR_ANY;

    int opt = 1;
    int addrlen = sizeof(addr);

    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR | SO_REUSEPORT, &opt, sizeof(opt))) {
        fprintf(stderr, "Error in setsockopt\n");
        close(server_fd);
        return -1;
    }

    if (bind(server_fd, (struct sockaddr *)&addr, sizeof(addr))<0) {
        fprintf(stderr, "Error binding \n");
        close(server_fd);
        return -1;
    }

    if (listen(server_fd, 10) < 0) { // Listen for up to 10 connections
        fprintf(stderr, "Error listening for connections\n");
        close(server_fd);
        return -1;
    }

    return server_fd;
}

int send_success_message(int client_sock) {
    int number = 6;
    int32_t net_number = htonl(number);  // Convert to network byte order
    if (send(client_sock, &net_number, sizeof(net_number), 0) < 0) {
        perror("Failed to send number");
        return -1;
    }
    return 0;
}

int receive_file(int client_sock, int total_requests) {
    struct timespec start, end;
    int64_t elapsed_time_ns = 0;

    int file_size = 0;
    if (read(client_sock, &file_size, sizeof(file_size)) < 0) {
        perror("Failed to read file size");
        return -1;
    }

    if (file_size < 8 || file_size > MAX_FILE_SIZE) {
        printf("file size %d\n", file_size);
        fprintf(stderr, "Received file size is out of the expected range (1kB to 1024kB)\n");
        return -1;
    }
    printf("Received file size: %d\n", file_size);
    
    char* buffer = malloc(PAGE_SIZE);
    if (!buffer) {
        perror("Failed to allocate buffer");
        return -1;
    }

    for(int i = 1; i <= total_requests; ++i){
        int total_bytes_received = 0;
        int bytes_received = 0;
        while(total_bytes_received < file_size){
            bytes_received = read(client_sock, buffer, PAGE_SIZE);
            if (bytes_received < 0) {
                perror("Error receiving data");
                free(buffer);
                return -1;
            }
            if (bytes_received == 0) {
                fprintf(stderr, "Connection closed by peer\n");
                free(buffer);
                return -1;
            }
            total_bytes_received += bytes_received;
        }

        if (total_bytes_received != file_size) {
            fprintf(stderr, "Mismatch in the file size received and expected\n");
            free(buffer);
            return -1;
        } else {
            if (send_success_message(client_sock) < 0) {
                free(buffer);
                return -1;  // handle error appropriately
            }
        }
        if (i % 10 == 0){
            printf("%d/100\n", i / 10);
        }
    }
    free(buffer);
    return 0;
}

void *handle_client(void *args) {
    struct thread_args *targs = (struct thread_args *)args;
    int client_sock = targs->client_sock;
    int total_requests = targs->total_requests;
    free(targs);

    printf("Connected to client\n");

    if (receive_file(client_sock, total_requests) < 0) {
        fprintf(stderr, "Failed to receive file\n");
    }

    close(client_sock);
    return NULL;
}

int main(int argc, const char** argv) {
    
    if (argc != 4) {
        fprintf(stderr, "Invalid arguments: must be port and total requests and number of threads.\n");
        exit(1);
    }

    char *endptr = NULL;

    // Convert PORT to int
    int PORT = strtol(argv[1], &endptr, 10);
    if (*endptr != '\0') {
        fprintf(stderr, "Invalid PORT: %s\n", argv[1]);
        exit(1);
    }

    // Convert total_requests to int
    int total_requests = strtol(argv[2], &endptr, 10);
    if (*endptr != '\0') {
        fprintf(stderr, "Invalid total_requests: %s\n", argv[2]);
        exit(1);
    }

    // Convert total_requests to int
    int num_of_threads = strtol(argv[3], &endptr, 10);
    if (*endptr != '\0') {
        fprintf(stderr, "Invalid number of threads: %s\n", argv[2]);
        exit(1);
    }

    int server_fd = listen_to_client(PORT);
    if (server_fd == -1){
        fprintf(stderr, "Error listening to client\n");
        return -1;
    }

    printf("Server is listening on port %d\n", PORT);

    
    int total = 0;
    while (1) {
        struct sockaddr_in addr;
        int addrlen = sizeof(addr);

        int *client_sock = malloc(sizeof(int));
        if (client_sock == NULL) {
            perror("Failed to allocate memory for client socket");
            continue;
        }
        
        *client_sock = accept(server_fd, (struct sockaddr *)&addr, (socklen_t*)&addrlen);
        if (*client_sock < 0) {
            perror("Error accepting connection");
            free(client_sock);
            continue;
        }

        pthread_t thread_id;
        struct thread_args *targs = malloc(sizeof(struct thread_args));
        if (targs == NULL) {
            perror("Failed to allocate memory for thread arguments");
            close(*client_sock);
            free(client_sock);
            continue;
        }
        
        targs->client_sock = *client_sock;
        targs->total_requests = total_requests/num_of_threads;
        printf("The %dth thread\n", total);
        total++;
        
        if (pthread_create(&thread_id, NULL, handle_client, (void *)targs) != 0) {
            perror("Failed to create thread");
            close(targs->client_sock);
            free(targs);
            continue;
        }
    }

    close(server_fd);
    return 0;
}