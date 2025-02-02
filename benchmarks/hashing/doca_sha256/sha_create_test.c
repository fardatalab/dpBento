/*
 * Copyright (c) 2022 NVIDIA CORPORATION & AFFILIATES, ALL RIGHTS RESERVED.
 *
 * This software product is a proprietary product of NVIDIA CORPORATION &
 * AFFILIATES (the "Company") and all right, title, and interest in and to the
 * software product, including all associated intellectual property rights, are
 * and shall remain exclusively with the Company.
 *
 * This software product is governed by the End User License Agreement
 * provided with the software product.
 *
 */

#include <string.h>
#include <stdlib.h>
#include <time.h>
#include <unistd.h>

#include <doca_buf.h>
#include <doca_buf_inventory.h>
#include <doca_ctx.h>
#include <doca_sha.h>
#include <doca_error.h>
#include <doca_log.h>

#include "common.h"

#define DOCA_SHA_JOB_TYPE DOCA_SHA_JOB_SHA256
#define ITERATION_COUNT 1000000
#define QUEUE_DEPTH 16

DOCA_LOG_REGISTER(SHA_CREATE);

#define SLEEP_IN_NANOS (10 * 1000) /* Sample the job every 10 microseconds  */

/*
 * Free callback - free doca_buf allocated pointer
 *
 * @addr [in]: Memory range pointer
 * @len [in]: Memory range length
 * @opaque [in]: An opaque pointer passed to iterator
 */
void
free_cb(void *addr, size_t len, void *opaque)
{
	(void)len;
	(void)opaque;

	free(addr);
}

/*
 * Clean all the sample resources
 *
 * @state [in]: program_core_objects struct
 * @sha_ctx [in]: SHA context
 */
static void
sha_cleanup(struct program_core_objects *state, struct doca_sha *sha_ctx)
{
	doca_error_t result;

	destroy_core_objects(state);

	result = doca_sha_destroy(sha_ctx);
	if (result != DOCA_SUCCESS)
		DOCA_LOG_ERR("Failed to destroy sha: %s", doca_get_error_string(result));
}

/**
 * Check if given device is capable of executing a DOCA_SHA_JOB_TYPE job with HW.
 *
 * @devinfo [in]: The DOCA device information
 * @return: DOCA_SUCCESS on success and DOCA_ERROR otherwise.
 */
static doca_error_t
job_sha_hardware_is_supported(struct doca_devinfo *devinfo)
{
	doca_error_t result;

	result = doca_sha_job_get_supported(devinfo, DOCA_SHA_JOB_TYPE);
	if (result != DOCA_SUCCESS)
		return result;

	doca_error_t ret = doca_sha_get_hardware_supported(devinfo);
	if (ret == DOCA_SUCCESS) {
		printf("sha supported\n");
	}
	else {
		printf("!!!sha hardware NOT supported!!!\n");
	}
	uint64_t maxbufsize;
	uint32_t minbufsize;
	doca_sha_get_max_src_buffer_size(devinfo, &maxbufsize);
	doca_sha_get_min_dst_buffer_size(devinfo, DOCA_SHA_JOB_TYPE, &minbufsize);
	printf("max src buf size = %ld, min dst buf size = %d\n", maxbufsize, minbufsize);
	return ret;
}

/**
 * Check if given device is capable of executing a DOCA_SHA_JOB_TYPE job with SW.
 *
 * @devinfo [in]: The DOCA device information
 * @return: DOCA_SUCCESS on success and DOCA_ERROR otherwise.
 */
static doca_error_t
job_sha_software_is_supported(struct doca_devinfo *devinfo)
{
	return doca_sha_job_get_supported(devinfo, DOCA_SHA_JOB_TYPE);
}

/*
 * Run sha_create sample
 *
 * @src_buffer [in]: source data for the SHA job
 * @return: DOCA_SUCCESS on success and DOCA_ERROR otherwise.
 */
doca_error_t
sha_create(char *src_buffer)
{
	struct program_core_objects state = {0};
	struct doca_event event = {0};
	struct doca_sha *sha_ctx;
	// struct doca_buf *src_doca_buf;
	// struct doca_buf *dst_doca_buf;
	struct doca_buf *src_doca_bufs[QUEUE_DEPTH];
	struct doca_buf *dst_doca_bufs[QUEUE_DEPTH];
	int src_buffers_len = QUEUE_DEPTH * (strlen(src_buffer) + 1);
	char *src_buffers = malloc(src_buffers_len);
	for (size_t i = 0; i < QUEUE_DEPTH; i++)
	{
		strcpy(src_buffers + i * (strlen(src_buffer)+1), src_buffer);
	}

	doca_error_t result;
	uint32_t workq_depth = QUEUE_DEPTH;		/* will queue this many sha job */
	uint32_t max_bufs = 2 * QUEUE_DEPTH;	/* will use 2*QUEUE_DEPTH doca buffers */
	char *dst_buffer = NULL;

	// timings
	struct timespec start_time, complete_time;
	double elpased_submit, elapsed_complete;
	clock_gettime(CLOCK_MONOTONIC, &start_time);

	// struct timespec ts = {
	// 	.tv_sec = 0,
	// 	.tv_nsec = SLEEP_IN_NANOS,
	// };

	struct doca_sha_job *sha_jobs = malloc(QUEUE_DEPTH * sizeof(struct doca_sha_job));
	for (size_t i = 0; i < QUEUE_DEPTH; i++)
	{
		sha_jobs[i] = (struct doca_sha_job) {
			.base = (struct doca_job) {
				.type = DOCA_SHA_JOB_TYPE,
				.flags = DOCA_JOB_FLAGS_NONE,
				.ctx = state.ctx,
				.user_data.u64 = i,
			},
			.resp_buf = dst_doca_bufs[i],
			.req_buf = src_doca_bufs[i],
			.flags = DOCA_SHA_JOB_FLAGS_NONE,
		};
	}
	// printf("malloc sha_jobs\n");

	/* Engine outputs hex format. For char format output, we need double the length */
	char sha_output[DOCA_SHA256_BYTE_COUNT * 2 + 1] = {0};
	uint8_t *resp_head;

	result = doca_sha_create(&sha_ctx);
	if (result != DOCA_SUCCESS) {
		DOCA_LOG_ERR("Unable to create sha engine: %s", doca_get_error_string(result));
		return result;
	}

	state.ctx = doca_sha_as_ctx(sha_ctx);

	result = open_doca_device_with_capabilities(&job_sha_hardware_is_supported, &state.dev);
	if (result != DOCA_SUCCESS) {
		result = open_doca_device_with_capabilities(&job_sha_software_is_supported, &state.dev);
		if (result != DOCA_SUCCESS) {
			DOCA_LOG_ERR("Failed to find device for SHA job");
			result = doca_sha_destroy(sha_ctx);
			return result;
		}
		DOCA_LOG_WARN("SHA engine is not enabled, using openssl instead");
	}


	result = init_core_objects(&state, workq_depth, max_bufs);
	if (result != DOCA_SUCCESS) {
		sha_cleanup(&state, sha_ctx);
		return result;
	}

	// dst_buffer = calloc(1, DOCA_SHA256_BYTE_COUNT);
	dst_buffer = calloc(QUEUE_DEPTH, DOCA_SHA256_BYTE_COUNT);
	if (dst_buffer == NULL) {
		DOCA_LOG_ERR("Failed to allocate memory");
		sha_cleanup(&state, sha_ctx);
		return DOCA_ERROR_NO_MEMORY;
	}

	result = doca_mmap_set_memrange(state.dst_mmap, dst_buffer, QUEUE_DEPTH * DOCA_SHA256_BYTE_COUNT);
	if (result != DOCA_SUCCESS) {
		free(dst_buffer);
		sha_cleanup(&state, sha_ctx);
		return result;
	}

	result = doca_mmap_set_free_cb(state.dst_mmap, &free_cb, NULL);
	if (result != DOCA_SUCCESS) {
		free(dst_buffer);
		sha_cleanup(&state, sha_ctx);
		return result;
	}

	result = doca_mmap_start(state.dst_mmap);
	if (result != DOCA_SUCCESS) {
		free(dst_buffer);
		sha_cleanup(&state, sha_ctx);
		return result;
	}

	result = doca_mmap_set_memrange(state.src_mmap, src_buffers, QUEUE_DEPTH * (strlen(src_buffer)+1));
	if (result != DOCA_SUCCESS) {
		sha_cleanup(&state, sha_ctx);
		return result;
	}

	result = doca_mmap_start(state.src_mmap);
	if (result != DOCA_SUCCESS) {
		sha_cleanup(&state, sha_ctx);
		return result;
	}

	/* Construct DOCA buffer for each address range */
	
	// result = doca_buf_inventory_buf_by_addr(state.buf_inv, state.src_mmap, src_buffer, strlen(src_buffer),
	// 					&src_doca_buf);
	for (size_t i = 0; i < QUEUE_DEPTH; i++)
	{
		// printf("src inventory %ld\n", i);
		result = doca_buf_inventory_buf_by_addr(state.buf_inv, state.src_mmap,
			src_buffers + i * (strlen(src_buffer)+1), strlen(src_buffer)+1, &src_doca_bufs[i]);
		if (result != DOCA_SUCCESS) {
			DOCA_LOG_ERR("Unable to acquire DOCA buffer representing source buffer: %s", doca_get_error_string(result));
			sha_cleanup(&state, sha_ctx);
			return result;
		}
		result = doca_buf_set_data(src_doca_bufs[i], src_buffers + i * (strlen(src_buffer)+1), strlen(src_buffer)+1);
		if (result != DOCA_SUCCESS) {
			DOCA_LOG_ERR("doca_buf_set_data() for request doca_buf failure");
			doca_buf_refcount_rm(src_doca_bufs[i], NULL);
			sha_cleanup(&state, sha_ctx);
			return result;
		}

		// printf("dst inventory %ld\n", i);
		result = doca_buf_inventory_buf_by_addr(state.buf_inv, state.dst_mmap,
			dst_buffer + i * DOCA_SHA256_BYTE_COUNT, DOCA_SHA256_BYTE_COUNT, &dst_doca_bufs[i]);
		if (result != DOCA_SUCCESS) {
			DOCA_LOG_ERR("Unable to acquire DOCA buffer representing dst buffer: %s", doca_get_error_string(result));
			sha_cleanup(&state, sha_ctx);
			return result;
		}
		/* result = doca_buf_set_data(dst_doca_bufs[i], dst_buffer + i * DOCA_SHA256_BYTE_COUNT, DOCA_SHA256_BYTE_COUNT);
		if (result != DOCA_SUCCESS) {
			DOCA_LOG_ERR("doca_buf_set_data() for request doca_buf failure");
			doca_buf_refcount_rm(src_doca_bufs[i], NULL);
			sha_cleanup(&state, sha_ctx);
			return result;
		} */
	}
	
	// result = doca_buf_inventory_buf_by_addr(state.buf_inv, state.src_mmap, src_buffers, src_buffers_len,
	// 					&src_doca_bufs);
	// if (result != DOCA_SUCCESS) {
	// 	DOCA_LOG_ERR("Unable to acquire DOCA buffer representing source buffer: %s", doca_get_error_string(result));
	// 	sha_cleanup(&state, sha_ctx);
	// 	return result;
	// }
	// /* Set data address and length in the doca_buf */
	// result = doca_buf_set_data(src_doca_buf, src_buffer, strlen(src_buffer));
	// if (result != DOCA_SUCCESS) {
	// 	DOCA_LOG_ERR("doca_buf_set_data() for request doca_buf failure");
	// 	doca_buf_refcount_rm(src_doca_buf, NULL);
	// 	sha_cleanup(&state, sha_ctx);
	// 	return result;
	// }

	/* Construct DOCA buffer for each address range */
	// result = doca_buf_inventory_buf_by_addr(state.buf_inv, state.dst_mmap, dst_buffer, DOCA_SHA256_BYTE_COUNT,
	// 					&dst_doca_buf);
	// if (result != DOCA_SUCCESS) {
	// 	DOCA_LOG_ERR("Unable to acquire DOCA buffer representing destination buffer: %s", doca_get_error_string(result));
	// 	doca_buf_refcount_rm(src_doca_buf, NULL);
	// 	sha_cleanup(&state, sha_ctx);
	// 	return result;
	// }

	size_t i_u64;
	// fill up the queue
	for (size_t i = 0; i < QUEUE_DEPTH; i++)
	{
		/* Construct sha job */
		sha_jobs[i] = (struct doca_sha_job) {
			.base = (struct doca_job) {
				.type = DOCA_SHA_JOB_TYPE,
				.flags = DOCA_JOB_FLAGS_NONE,
				.ctx = state.ctx,
				.user_data.u64 = i,
			},
			.resp_buf = dst_doca_bufs[i],
			.req_buf = src_doca_bufs[i],
			.flags = DOCA_SHA_JOB_FLAGS_NONE,
		};

		/* Enqueue sha job */
		result = doca_workq_submit(state.workq, &sha_jobs[i].base);
		// printf("submit job %ld\n", i);
		if (result != DOCA_SUCCESS) {
			DOCA_LOG_ERR("Failed to submit sha job: %d: %s", result, doca_get_error_string(result));
			doca_buf_refcount_rm(dst_doca_bufs[i], NULL);
			doca_buf_refcount_rm(src_doca_bufs[i], NULL);
			sha_cleanup(&state, sha_ctx);
			return result;
		}
	}


	// enqueue more jobs
	struct doca_sha_job *this_sha_job;
	for (size_t i = 0; i < ITERATION_COUNT - QUEUE_DEPTH; i++)
	{
		/* Wait for job completion */
		while ((result = doca_workq_progress_retrieve(state.workq, &event, DOCA_WORKQ_RETRIEVE_FLAGS_NONE)) ==
				DOCA_ERROR_AGAIN) {
			//nanosleep(&ts, &ts);
		}

		if (result != DOCA_SUCCESS) {
			DOCA_LOG_ERR("Failed to retrieve sha job: %s", doca_get_error_string(result));
		}

		/* else if (((int)(event.type) != (int)DOCA_SHA_JOB_TYPE) ||
			(event.user_data.u64 != DOCA_SHA_JOB_TYPE))
			DOCA_LOG_ERR("Received wrong event"); */

		else {
			/* doca_buf_get_data(sha_job.resp_buf, (void **)&resp_head);
			for (i = 0; i < DOCA_SHA256_BYTE_COUNT; i++)
				snprintf(sha_output + (2 * i), 3, "%02x", resp_head[i]);
			DOCA_LOG_INFO("SHA256 output of src of size %ld is: %s", strlen(src_buffer), sha_output); */
		}

		i_u64 = event.user_data.u64;
		// printf("job %ld completed\n", i_u64);

		uint16_t prev_refcnt;
		if (doca_buf_refcount_rm(src_doca_bufs[i_u64], &prev_refcnt) != DOCA_SUCCESS ||
		doca_buf_refcount_rm(dst_doca_bufs[i_u64], NULL) != DOCA_SUCCESS)
		DOCA_LOG_ERR("Failed to decrease DOCA buffer reference count");
		// printf("prev refcnt %d\n", prev_refcnt);

		this_sha_job = &sha_jobs[i_u64];

		result = doca_buf_inventory_buf_by_addr(state.buf_inv, state.src_mmap,
			src_buffers + i_u64 * (strlen(src_buffer)+1), strlen(src_buffer)+1, &src_doca_bufs[i_u64]);
		if (result != DOCA_SUCCESS) {
			DOCA_LOG_ERR("Unable to acquire DOCA buffer representing source buffer: %s", doca_get_error_string(result));
			sha_cleanup(&state, sha_ctx);
			return result;
		}

		result = doca_buf_inventory_buf_by_addr(state.buf_inv, state.dst_mmap,
			dst_buffer + i_u64 * DOCA_SHA256_BYTE_COUNT, DOCA_SHA256_BYTE_COUNT, &dst_doca_bufs[i_u64]);
		if (result != DOCA_SUCCESS) {
			DOCA_LOG_ERR("Unable to acquire DOCA buffer representing dst buffer: %s", doca_get_error_string(result));
			sha_cleanup(&state, sha_ctx);
			return result;
		}

		/* Construct sha job */
		sha_jobs[i_u64] = (struct doca_sha_job) {
			.base = (struct doca_job) {
				.type = DOCA_SHA_JOB_TYPE,
				.flags = DOCA_JOB_FLAGS_NONE,
				.ctx = state.ctx,
				.user_data.u64 = i_u64,
			},
			.resp_buf = dst_doca_bufs[i_u64],
			.req_buf = src_doca_bufs[i_u64],
			.flags = DOCA_SHA_JOB_FLAGS_NONE,
		};

		/* Enqueue sha job */
		result = doca_workq_submit(state.workq, &sha_jobs[i_u64].base);//&(this_sha_job->base)
		if (result != DOCA_SUCCESS) {
			DOCA_LOG_ERR("Failed to submit sha job: %s", doca_get_error_string(result));
			doca_buf_refcount_rm(dst_doca_bufs[i_u64], NULL);
			doca_buf_refcount_rm(src_doca_bufs[i_u64], NULL);
			sha_cleanup(&state, sha_ctx);
			return result;
		}
		// printf("submit job %ld\n", i_u64);
	}

	for (size_t i = 0; i < QUEUE_DEPTH; i++)
	{
		/* Wait for job completion */
		while ((result = doca_workq_progress_retrieve(state.workq, &event, DOCA_WORKQ_RETRIEVE_FLAGS_NONE)) ==
				DOCA_ERROR_AGAIN) {
			//nanosleep(&ts, &ts);
		}

		if (result != DOCA_SUCCESS) {
			DOCA_LOG_ERR("Failed to retrieve sha job: %s", doca_get_error_string(result));
		}

		/* else if (((int)(event.type) != (int)DOCA_SHA_JOB_TYPE) ||
			(event.user_data.u64 != DOCA_SHA_JOB_TYPE))
			DOCA_LOG_ERR("Received wrong event"); */

		else {
			/* doca_buf_get_data(sha_job.resp_buf, (void **)&resp_head);
			for (i = 0; i < DOCA_SHA256_BYTE_COUNT; i++)
				snprintf(sha_output + (2 * i), 3, "%02x", resp_head[i]);
			DOCA_LOG_INFO("SHA256 output of src of size %ld is: %s", strlen(src_buffer), sha_output); */
		}

		i_u64 = event.user_data.u64;
		// printf("job %ld completed\n", i_u64);

		uint16_t prev_refcnt;
		if (doca_buf_refcount_rm(src_doca_bufs[i_u64], &prev_refcnt) != DOCA_SUCCESS ||
		doca_buf_refcount_rm(dst_doca_bufs[i_u64], NULL) != DOCA_SUCCESS)
		DOCA_LOG_ERR("Failed to decrease DOCA buffer reference count");
		// printf("final wait pass, prev refcnt %d\n", prev_refcnt);

	}

	clock_gettime(CLOCK_MONOTONIC, &complete_time);
	elapsed_complete = complete_time.tv_sec - start_time.tv_sec;
	elapsed_complete += (complete_time.tv_nsec - start_time.tv_nsec) / 1000000000.0;
	printf("total completion time: %f\n", elapsed_complete);
	
	/* Clean and destroy all relevant objects */
	sha_cleanup(&state, sha_ctx);
	
	
	// /* Construct sha job */
	// const struct doca_sha_job sha_job = {
	// 	.base = (struct doca_job) {
	// 		.type = DOCA_SHA_JOB_TYPE,
	// 		.flags = DOCA_JOB_FLAGS_NONE,
	// 		.ctx = state.ctx,
	// 		.user_data.u64 = DOCA_SHA_JOB_TYPE,
	// 		},
	// 	.resp_buf = dst_doca_buf,
	// 	.req_buf = src_doca_buf,
	// 	.flags = DOCA_SHA_JOB_FLAGS_NONE,
	// };

	// /* Enqueue sha job */

	// // time submit
	// struct timespec submit_start, submit_end, completed;
	// double elpased_submit, elapsed_complete;
	// clock_gettime(CLOCK_MONOTONIC, &submit_start);

	// result = doca_workq_submit(state.workq, &sha_job.base);
	// if (result != DOCA_SUCCESS) {
	// 	DOCA_LOG_ERR("Failed to submit sha job: %s", doca_get_error_string(result));
	// 	doca_buf_refcount_rm(dst_doca_buf, NULL);
	// 	doca_buf_refcount_rm(src_doca_buf, NULL);
	// 	sha_cleanup(&state, sha_ctx);
	// 	return result;
	// }
	// clock_gettime(CLOCK_MONOTONIC, &submit_end);
	// elpased_submit = submit_end.tv_sec - submit_start.tv_sec;
	// elpased_submit += (submit_end.tv_nsec - submit_start.tv_nsec) / 1000000000.0;
	// printf("submit time: %f\n", elpased_submit);

	// /* Wait for job completion */
	// while ((result = doca_workq_progress_retrieve(state.workq, &event, DOCA_WORKQ_RETRIEVE_FLAGS_NONE)) ==
	//        DOCA_ERROR_AGAIN) {
	// 	//nanosleep(&ts, &ts);
	// }

	// clock_gettime(CLOCK_MONOTONIC, &completed);
	// elapsed_complete = completed.tv_sec - submit_end.tv_sec;
	// elapsed_complete += (completed.tv_nsec - submit_end.tv_nsec) / 1000000000.0;
	// printf("completion time: %f, total = %f\n", elapsed_complete, elapsed_complete + elpased_submit);

	// if (result != DOCA_SUCCESS)
	// 	DOCA_LOG_ERR("Failed to retrieve sha job: %s", doca_get_error_string(result));

	// else if (event.result.u64 != DOCA_SUCCESS)
	// 	DOCA_LOG_ERR("SHA job finished unsuccessfully");

	// else if (((int)(event.type) != (int)DOCA_SHA_JOB_TYPE) ||
	// 	(event.user_data.u64 != DOCA_SHA_JOB_TYPE))
	// 	DOCA_LOG_ERR("Received wrong event");

	// else {
	// 	doca_buf_get_data(sha_job.resp_buf, (void **)&resp_head);
	// 	for (i = 0; i < DOCA_SHA256_BYTE_COUNT; i++)
	// 		snprintf(sha_output + (2 * i), 3, "%02x", resp_head[i]);
	// 	DOCA_LOG_INFO("SHA256 output of src of size %ld is: %s", strlen(src_buffer), sha_output);
	// 	// DOCA_LOG_INFO("SHA256 output is: %s", sha_output);
	// }

	// if (doca_buf_refcount_rm(src_doca_buf, NULL) != DOCA_SUCCESS ||
	//     doca_buf_refcount_rm(dst_doca_buf, NULL) != DOCA_SUCCESS)
	// 	DOCA_LOG_ERR("Failed to decrease DOCA buffer reference count");

	// /* Clean and destroy all relevant objects */
	// sha_cleanup(&state, sha_ctx);

	return result;
}
