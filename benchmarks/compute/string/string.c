#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define OPTIMIZE3 __attribute__((optimize("-O3")));
#define LOOP_TIMES 100000000
int STR1LEN;
int STR2LEN;
int STRDSTLEN;

#pragma GCC push_options
#pragma GCC optimize("O1")

// Define a function to generate a random string
void generate_random_string(char *str, size_t len)
{
    const char charset[] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    for (size_t i = 0; i < len - 1; i++)
    {
        str[i] = charset[rand() % (sizeof(charset) - 1)];
    }
    str[len - 1] = '\0';
}

// Test the performance of strcpy
static void test_strcpy()
{
    char str1[STR1LEN], str2[STR2LEN], dst[STRDSTLEN];
    generate_random_string(str1, sizeof(str1));
    generate_random_string(str2, sizeof(str2));

    struct timespec start_time, end_time;
    clock_gettime(CLOCK_MONOTONIC, &start_time);

    for (size_t i = 0; i < LOOP_TIMES; i++)
    {
        strcpy(dst, str1);
        strcpy(dst, str2);
    }

    clock_gettime(CLOCK_MONOTONIC, &end_time);

    double t = (end_time.tv_sec - start_time.tv_sec) * 1e9;
    t += (end_time.tv_nsec - start_time.tv_nsec);
    double throughput = LOOP_TIMES / (t / 1e6);

    printf("strcpy throughput ops/ms: %f\n", throughput);
}

// Test the performance of strcat
static void test_strcat()
{
    char str1[STR1LEN], str2[STR2LEN], dst[STRDSTLEN];
    generate_random_string(str1, sizeof(str1));
    generate_random_string(str2, sizeof(str2));

    struct timespec start_time, end_time;
    clock_gettime(CLOCK_MONOTONIC, &start_time);

    for (size_t i = 0; i < LOOP_TIMES; i++)
    {
        strcpy(dst, "");
        strcat(dst, str1);
        strcpy(dst, "");
        strcat(dst, str2);
    }

    clock_gettime(CLOCK_MONOTONIC, &end_time);

    double t = (end_time.tv_sec - start_time.tv_sec) * 1e9;
    t += (end_time.tv_nsec - start_time.tv_nsec);
    double throughput = LOOP_TIMES / (t / 1e6);

    printf("strcat throughput ops/ms: %f\n", throughput);
}

// Test the performance of strcmp
static void test_strcmp()
{
    char str1[STR1LEN], str2[STR2LEN];
    generate_random_string(str1, sizeof(str1));
    generate_random_string(str2, sizeof(str2));

    struct timespec start_time, end_time;
    clock_gettime(CLOCK_MONOTONIC, &start_time);

    for (size_t i = 0; i < LOOP_TIMES; i++)
    {
        strcmp(str1, str1);
        strcmp(str2, str2);
        strcmp(str1, str2);
        strcmp(str2, str1);
    }

    clock_gettime(CLOCK_MONOTONIC, &end_time);

    double t = (end_time.tv_sec - start_time.tv_sec) * 1e9;
    t += (end_time.tv_nsec - start_time.tv_nsec);
    double throughput = LOOP_TIMES / (t / 1e6);

    printf("strcmp throughput ops/ms: %f\n", throughput);
}

// Test the performance of strncat
static void test_strncat()
{
    char str1[STR1LEN], str2[STR2LEN], dst[STRDSTLEN];
    generate_random_string(str1, sizeof(str1));
    generate_random_string(str2, sizeof(str2));

    struct timespec start_time, end_time;
    clock_gettime(CLOCK_MONOTONIC, &start_time);

    for (size_t i = 0; i < LOOP_TIMES; i++)
    {
        strcpy(dst, "");
        strncat(dst, str1, sizeof(str1));
        strcpy(dst, "");
        strncat(dst, str2, sizeof(str2));
    }

    clock_gettime(CLOCK_MONOTONIC, &end_time);

    double t = (end_time.tv_sec - start_time.tv_sec) * 1e9;
    t += (end_time.tv_nsec - start_time.tv_nsec);
    double throughput = LOOP_TIMES / (t / 1e6);

    printf("strncat throughput ops/ms: %f\n", throughput);
}

// Test the performance of strncmp
static void test_strncmp()
{
    char str1[STR1LEN], str2[STR2LEN];
    generate_random_string(str1, sizeof(str1));
    generate_random_string(str2, sizeof(str2));

    struct timespec start_time, end_time;
    clock_gettime(CLOCK_MONOTONIC, &start_time);

    for (size_t i = 0; i < LOOP_TIMES; i++)
    {
        strncmp(str1, str1, sizeof(str1));
        strncmp(str2, str2, sizeof(str2));
        strncmp(str1, str2, sizeof(str2));
        strncmp(str2, str1, sizeof(str1));
    }

    clock_gettime(CLOCK_MONOTONIC, &end_time);

    double t = (end_time.tv_sec - start_time.tv_sec) * 1e9;
    t += (end_time.tv_nsec - start_time.tv_nsec);
    double throughput = LOOP_TIMES / (t / 1e6);

    printf("strncmp throughput ops/ms: %f\n", throughput);
}

// Test the performance of strcoll
static void test_strcoll()
{
    char str1[STR1LEN], str2[STR2LEN];
    generate_random_string(str1, sizeof(str1));
    generate_random_string(str2, sizeof(str2));

    struct timespec start_time, end_time;
    clock_gettime(CLOCK_MONOTONIC, &start_time);

    for (size_t i = 0; i < LOOP_TIMES; i++)
    {
        strcoll(str1, str1);
        strcoll(str2, str2);
        strcoll(str1, str2);
        strcoll(str2, str1);
    }

    clock_gettime(CLOCK_MONOTONIC, &end_time);

    double t = (end_time.tv_sec - start_time.tv_sec) * 1e9;
    t += (end_time.tv_nsec - start_time.tv_nsec);
    double throughput = LOOP_TIMES / (t / 1e6);

    printf("strcoll throughput ops/ms: %f\n", throughput);
}

// Test the performance of strlen
static void test_strlen()
{
    char str1[STR1LEN], str2[STR2LEN];
    generate_random_string(str1, sizeof(str1));
    generate_random_string(str2, sizeof(str2));

    struct timespec start_time, end_time;
    clock_gettime(CLOCK_MONOTONIC, &start_time);

    for (size_t i = 0; i < LOOP_TIMES; i++)
    {
        strlen(str1);
        strlen(str2);
    }

    clock_gettime(CLOCK_MONOTONIC, &end_time);

    double t = (end_time.tv_sec - start_time.tv_sec) * 1e9;
    t += (end_time.tv_nsec - start_time.tv_nsec);
    double throughput = LOOP_TIMES / (t / 1e6);

    printf("strlen throughput ops/ms: %f\n", throughput);
}

// Test the performance of strchr
static void test_strchr()
{
    char str1[STR1LEN], str2[STR2LEN];
    generate_random_string(str1, sizeof(str1));
    generate_random_string(str2, sizeof(str2));

    struct timespec start_time, end_time;
    clock_gettime(CLOCK_MONOTONIC, &start_time);

    for (size_t i = 0; i < LOOP_TIMES; i++)
    {
        strchr(str1, str1[0]);
        strchr(str2, str2[0]);
    }

    clock_gettime(CLOCK_MONOTONIC, &end_time);

    double t = (end_time.tv_sec - start_time.tv_sec) * 1e9;
    t += (end_time.tv_nsec - start_time.tv_nsec);
    double throughput = LOOP_TIMES / (t / 1e6);

    printf("strchr throughput ops/ms: %f\n", throughput);
}

// Test the performance of strrchr
static void test_strrchr()
{
    char str1[STR1LEN], str2[STR2LEN];
    generate_random_string(str1, sizeof(str1));
    generate_random_string(str2, sizeof(str2));

    struct timespec start_time, end_time;
    clock_gettime(CLOCK_MONOTONIC, &start_time);

    for (size_t i = 0; i < LOOP_TIMES; i++)
    {
        strrchr(str1, str1[0]);
        strrchr(str2, str2[0]);
    }

    clock_gettime(CLOCK_MONOTONIC, &end_time);

    double t = (end_time.tv_sec - start_time.tv_sec) * 1e9;
    t += (end_time.tv_nsec - start_time.tv_nsec);
    double throughput = LOOP_TIMES / (t / 1e6);

    printf("strrchr throughput ops/ms: %f\n", throughput);
}

// Test the performance of strxfrm
static void test_strxfrm()
{
    char str1[STR1LEN], str2[STR2LEN], dst[STRDSTLEN];
    generate_random_string(str1, sizeof(str1));
    generate_random_string(str2, sizeof(str2));

    struct timespec start_time, end_time;
    clock_gettime(CLOCK_MONOTONIC, &start_time);

    for (size_t i = 0; i < LOOP_TIMES; i++)
    {
        strxfrm(dst, str1, sizeof(dst));
        strxfrm(dst, str2, sizeof(dst));
    }

    clock_gettime(CLOCK_MONOTONIC, &end_time);

    double t = (end_time.tv_sec - start_time.tv_sec) * 1e9;
    t += (end_time.tv_nsec - start_time.tv_nsec);
    double throughput = LOOP_TIMES / (t / 1e6);

    printf("strxfrm throughput ops/ms: %f\n", throughput);
}

static void test_strstr()
{
    char str1[STR1LEN];
    char *str2;
    // str2[STR2LEN];
    generate_random_string(str1, sizeof(str1));
    // generate_random_string(str2, sizeof(str2));

    char *str2_ptrs[LOOP_TIMES];
    for (size_t j = 0; j < LOOP_TIMES; j++)
    {
        str2_ptrs[j] = rand() % (STR1LEN - STR2LEN) + str1;
    }

    struct timespec start_time, end_time;
    clock_gettime(CLOCK_MONOTONIC, &start_time);

    for (size_t i = 0; i < LOOP_TIMES; i++)
    {

        str2 = str2_ptrs[i];

        strstr(str1, str2);
    }

    clock_gettime(CLOCK_MONOTONIC, &end_time);

    double t = (end_time.tv_sec - start_time.tv_sec) * 1e9;
    t += (end_time.tv_nsec - start_time.tv_nsec);
    double throughput = LOOP_TIMES / (t / 1e6);

    printf("strstr throughput ops/ms: %f\n", throughput);
}

static void test_strstr_deprecated()
{
    char str1[STR1LEN];
    char *str2;
    // str2[STR2LEN];
    generate_random_string(str1, sizeof(str1));
    // generate_random_string(str2, sizeof(str2));

    char **str2_ptrs = (char **)malloc(LOOP_TIMES * sizeof(char *));

    for (size_t j = 0; j < LOOP_TIMES; j++)
    {
        str2_ptrs[j] = (char *)malloc(STR2LEN * sizeof(char));
        strncpy(str2_ptrs[j], rand() % (STR1LEN - STR2LEN) + str1, STR2LEN);
        // make sure the string is null-terminated
        str2_ptrs[j][STR2LEN - 1] = '\0';
    }

    struct timespec start_time, end_time;
    clock_gettime(CLOCK_MONOTONIC, &start_time);

    for (size_t i = 0; i < LOOP_TIMES; i++)
    {

        str2 = str2_ptrs[i];

        strstr(str1, str2);
    }

    clock_gettime(CLOCK_MONOTONIC, &end_time);

    double t = (end_time.tv_sec - start_time.tv_sec) * 1e9;
    t += (end_time.tv_nsec - start_time.tv_nsec);
    double throughput = LOOP_TIMES / (t / 1e6);

    printf("strstr throughput ops/ms: %f\n", throughput);
    // free the allocated memory
    for (size_t j = 0; j < LOOP_TIMES; j++)
    {
        free(str2_ptrs[j]);
    }
    free(str2_ptrs);
}

int main(int argc, char *argv[])
{
    if (argc > 1)
    {
        STR1LEN = atoi(argv[1]);
        STR2LEN = STR1LEN / 2;
        STRDSTLEN = STR1LEN + STR2LEN + 1;
    }
    else
    {
        STR1LEN = 10;
        STR2LEN = STR1LEN / 2;
        STRDSTLEN = STR1LEN + STR2LEN + 1;
        printf("Using default string length: %d\n", STR1LEN);
    }

    int lens[] = {10, 64, 256, 1024};

    srand(time(NULL));
    for (int i = 0; i < sizeof(lens) / sizeof(lens[0]); i++)
    {
        STR1LEN = lens[i];
        STR2LEN = STR1LEN / 2;
        STRDSTLEN = STR1LEN + STR2LEN + 1;
        test_strstr();
    }

    for (int i = 0; i < sizeof(lens) / sizeof(lens[0]); i++)
    {
        STR1LEN = lens[i];
        STR2LEN = STR1LEN / 2;
        STRDSTLEN = STR1LEN + STR2LEN + 1;

        test_strcpy();
    }

    for (int i = 0; i < sizeof(lens) / sizeof(lens[0]); i++)
    {
        STR1LEN = lens[i];
        STR2LEN = STR1LEN / 2;
        STRDSTLEN = STR1LEN + STR2LEN + 1;

        test_strcat();
    }

    for (int i = 0; i < sizeof(lens) / sizeof(lens[0]); i++)
    {
        STR1LEN = lens[i];
        STR2LEN = STR1LEN / 2;
        STRDSTLEN = STR1LEN + STR2LEN + 1;

        test_strcmp();
    }

    for (int i = 0; i < sizeof(lens) / sizeof(lens[0]); i++)
    {
        STR1LEN = lens[i];
        STR2LEN = STR1LEN / 2;
        STRDSTLEN = STR1LEN + STR2LEN + 1;

        test_strncat();
    }

    for (int i = 0; i < sizeof(lens) / sizeof(lens[0]); i++)
    {
        STR1LEN = lens[i];
        STR2LEN = STR1LEN / 2;
        STRDSTLEN = STR1LEN + STR2LEN + 1;

        test_strncmp();
    }

    for (int i = 0; i < sizeof(lens) / sizeof(lens[0]); i++)
    {
        STR1LEN = lens[i];
        STR2LEN = STR1LEN / 2;
        STRDSTLEN = STR1LEN + STR2LEN + 1;

        test_strcoll();
    }

    for (int i = 0; i < sizeof(lens) / sizeof(lens[0]); i++)
    {
        STR1LEN = lens[i];
        STR2LEN = STR1LEN / 2;
        STRDSTLEN = STR1LEN + STR2LEN + 1;

        test_strlen();
    }

    for (int i = 0; i < sizeof(lens) / sizeof(lens[0]); i++)
    {
        STR1LEN = lens[i];
        STR2LEN = STR1LEN / 2;
        STRDSTLEN = STR1LEN + STR2LEN + 1;

        test_strchr();
    }

    for (int i = 0; i < sizeof(lens) / sizeof(lens[0]); i++)
    {
        STR1LEN = lens[i];
        STR2LEN = STR1LEN / 2;
        STRDSTLEN = STR1LEN + STR2LEN + 1;

        test_strrchr();
    }

    for (int i = 0; i < sizeof(lens) / sizeof(lens[0]); i++)
    {
        STR1LEN = lens[i];
        STR2LEN = STR1LEN / 2;
        STRDSTLEN = STR1LEN + STR2LEN + 1;

        test_strxfrm();
    }
    return 0;
}

#pragma GCC pop_options