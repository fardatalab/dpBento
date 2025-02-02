#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <atomic>
// #include <pthread.h>
#include <thread>

#include <hs.h>
#include <chrono>
using std::chrono::high_resolution_clock;

// #define N_LINES_PER_BLOCK 5000


/**
 * Fill a data buffer from the given filename, returning it and filling @a
 * length with its length. Returns NULL on failure.
 */
static char *readInputData(const char *inputFN, unsigned int *length) {
    FILE *f = fopen(inputFN, "rb");
    if (!f) {
        fprintf(stderr, "ERROR: unable to open file \"%s\": %s\n", inputFN,
                strerror(errno));
        return NULL;
    }

    /* We use fseek/ftell to get our data length, in order to keep this example
     * code as portable as possible. */
    if (fseek(f, 0, SEEK_END) != 0) {
        fprintf(stderr, "ERROR: unable to seek file \"%s\": %s\n", inputFN,
                strerror(errno));
        fclose(f);
        return NULL;
    }
    long dataLen = ftell(f);
    if (dataLen < 0) {
        fprintf(stderr, "ERROR: ftell() failed: %s\n", strerror(errno));
        fclose(f);
        return NULL;
    }
    if (fseek(f, 0, SEEK_SET) != 0) {
        fprintf(stderr, "ERROR: unable to seek file \"%s\": %s\n", inputFN,
                strerror(errno));
        fclose(f);
        return NULL;
    }

    /* Hyperscan's hs_scan function accepts length as an unsigned int, so we
     * limit the size of our buffer appropriately. */
    if ((unsigned long)dataLen > UINT_MAX) {
        dataLen = UINT_MAX;
        printf("WARNING: clipping data to %ld bytes\n", dataLen);
    } else if (dataLen == 0) {
        fprintf(stderr, "ERROR: input file \"%s\" is empty\n", inputFN);
        fclose(f);
        return NULL;
    }

    char *inputData = (char *) malloc(dataLen);
    if (!inputData) {
        fprintf(stderr, "ERROR: unable to malloc %ld bytes\n", dataLen);
        fclose(f);
        return NULL;
    }

    char *p = inputData;
    size_t bytesLeft = dataLen;
    while (bytesLeft) {
        size_t bytesRead = fread(p, 1, bytesLeft, f);
        bytesLeft -= bytesRead;
        p += bytesRead;
        if (ferror(f) != 0) {
            fprintf(stderr, "ERROR: fread() failed\n");
            free(inputData);
            fclose(f);
            return NULL;
        }
    }

    fclose(f);

    *length = (unsigned int)dataLen;
    return inputData;
}



bool handler_to_run = true;

std::atomic_int matches = 0;

uint like_copper_matches = 0;
uint not_like_economy_polished_matches = 0;
uint eq_economy_anodized_steel_matches = 0;
uint phone_substring_matches = 0;
uint p_container_in_matches = 0;

std::chrono::nanoseconds regex_duration{0};
std::chrono::nanoseconds compile_duration{0};

std::chrono::nanoseconds like_copper_duration{0};
std::chrono::nanoseconds not_like_economy_polished_duration{0};
std::chrono::nanoseconds eq_economy_anodized_steel_duration{0};
std::chrono::nanoseconds phone_substring_duration{0};
std::chrono::nanoseconds p_container_in_duration{0};

static int eventHandler(unsigned int id, unsigned long long from,
                        unsigned long long to, unsigned int flags, void *ctx) {
    // printf("Match for pattern \"%s\" at offset %llu\n", (char *)ctx, to);
    matches++;
    return 0;
}

void scanInputData(hs_database_t *database, char *inputData, unsigned int length, char *pattern) {
        hs_scratch_t *scratch = NULL;
        if (hs_alloc_scratch(database, &scratch) != HS_SUCCESS) {
            fprintf(stderr, "ERROR: Unable to allocate scratch space. Exiting.\n");
            free(inputData);
            hs_free_database(database);
            return;
        }

        // printf("Scanning %s %u bytes with Hyperscan\n", inputFN, length);

        if (hs_scan(database, inputData, length, 0, scratch, eventHandler,
                    pattern) != HS_SUCCESS) {
            fprintf(stderr, "ERROR: Unable to scan input buffer. Exiting.\n");
            hs_free_scratch(scratch);
            free(inputData);
            hs_free_database(database);
            return;
        }
        // printf("matches: %u\n", matches);

        hs_free_scratch(scratch);        
    }

int main(int argc, char *argv[]) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <n_threads> <pattern> <input file>\n", argv[0]);
        return -1;
    }

    int n_threads = atoi(argv[1]);

    char *pattern = argv[2];
    // char *pattern = "([A-Z]| )+?COPPER";
    char *inputFN = argv[3];
    printf("Pattern: %s\n", pattern);

    /* First, we attempt to compile the pattern provided on the command line.
     * We assume 'DOTALL' semantics, meaning that the '.' meta-character will
     * match newline characters. The compiler will analyse the given pattern and
     * either return a compiled Hyperscan database, or an error message
     * explaining why the pattern didn't compile.
     */
    hs_database_t *database;
    hs_compile_error_t *compile_err;
    if (hs_compile(pattern, 0, HS_MODE_BLOCK, NULL, &database,
                   &compile_err) != HS_SUCCESS) {
        fprintf(stderr, "ERROR: Unable to compile pattern \"%s\": %s\n",
                pattern, compile_err->message);
        hs_free_compile_error(compile_err);
        return -1;
    }

    /* Next, we read the input data file into a buffer. */
    unsigned int length;
    char *inputData = readInputData(inputFN, &length);
    if (!inputData) {
        hs_free_database(database);
        return -1;
    }

    std::chrono::time_point<high_resolution_clock> start_time, end_time;
    start_time = high_resolution_clock::now();

    // use threads to scan the input data
    unsigned int length_per_thread = length / n_threads;
    std::thread threads[n_threads];
    for (int i = 0; i < n_threads; i++) {
        threads[i] = std::thread(scanInputData, database, inputData + i * length_per_thread, length_per_thread, pattern);
    }

    for (int i = 0; i < n_threads; i++) {
        threads[i].join();
    }
    
    end_time = high_resolution_clock::now();
    regex_duration += std::chrono::duration_cast<std::chrono::nanoseconds>(end_time - start_time);
    printf("matches: %u\n", matches.load());
    printf("duration (ns): %ld\n", regex_duration.count());

    

    /* Scanning is complete, any matches have been handled, so now we just
     * clean up and exit.
     */
    free(inputData);
    hs_free_database(database);
    return 0;
}
