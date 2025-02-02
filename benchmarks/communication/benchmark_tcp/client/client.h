/**
 * @file client.h
 * @brief Header file for client file-sending program.
 *
 * Contains function prototypes and the definition of `struct thread_args`
 * used in the multithreaded client for sending files and measuring latency/throughput.
 */

#ifndef CLIENT_H
#define CLIENT_H

#include <stdio.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <stdlib.h>
#include <pthread.h>
#include <time.h>
#include <string.h>

// Struct to hold thread-specific data
struct thread_args {
    int sockfd;                // Socket file descriptor for communication
    int file_size;             // Size of the file to send in bytes
    char *buffer;              // Pointer to the buffer containing file data
    int requests_per_thread;   // Number of requests this thread is responsible for
    double *latencies;         // Pointer to an array of latencies for performance measurement
    int thread_index;          // Index of the thread
};

/**
 * @brief Connect to a server using a specified IP address and port.
 *
 * This function creates a socket and attempts to connect to the server specified
 * by the IP address and port. If the connection is successful, it returns the 
 * socket file descriptor, which is used for subsequent communications.
 * 
 * @param server_ip The IP address of the server to connect to, in dotted decimal notation.
 * @param port The port number on which the server is listening.
 * 
 * @return On success, returns the socket file descriptor (sockfd).
 *         On failure, returns -1 and prints an error message.
 */
int connect_to_server(const char* server_ip, int port);

/**
 * @brief Validate a success message from the server.
 *
 * This function waits for a message from the server that confirms that the server
 * successfully received the data sent by the client. The success message is expected
 * to be an integer with the value 6, sent over the socket. If the validation fails, 
 * an error message is printed.
 * 
 * @param sock The socket file descriptor used for communication.
 * 
 * @return 0 if the success message is received correctly, -1 otherwise.
 */
int validate_success_message(int sock);

/**
 * @brief Send a file to the server over a socket.
 *
 * This function transmits the contents of a file, stored in a buffer, to the server 
 * in chunks. The file is sent over the socket in increments of PAGE_SIZE (4 KB) until
 * the entire file is transferred. After the file is sent, the function waits for 
 * a confirmation message from the server to validate the successful transmission.
 * 
 * @param sock The socket file descriptor used for communication.
 * @param file_size The size of the file being sent, in bytes.
 * @param buffer A pointer to the buffer containing the file data to be sent.
 * 
 * @return 0 if the file is sent and validated successfully, -1 otherwise.
 */
int send_file(int sock, int file_size, char *buffer);

/**
 * @brief Thread function for sending files and recording latencies.
 *
 * This function is executed by multiple threads, each responsible for sending a number
 * of file transmission requests. For each request, the latency (time taken to send the file)
 * is measured using `clock_gettime()`, and the latencies are stored in a shared array. 
 * Each thread operates on its own socket connection and sends files independently.
 * 
 * @param args A pointer to a `struct thread_args` containing thread-specific data,
 * including the socket file descriptor, file size, buffer, number of requests, and 
 * a latencies array for storing the results.
 * 
 * @return NULL upon completion or error.
 */
void *send_files(void *args);

#endif