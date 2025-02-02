#
# Copyright (c) 2022-2023 NVIDIA CORPORATION & AFFILIATES, ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of NVIDIA CORPORATION &
# AFFILIATES (the "Company") and all right, title, and interest in and to the
# software product, including all associated intellectual property rights, are
# and shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#

project('DOCA_REGEX', 'C', 'CPP',
	# Get version number from file.
	version: '0.1',
	license: 'Proprietary',
	default_options: ['buildtype=debug'],
	meson_version: '>= 0.61.2'
)

SAMPLE_NAME = 'regex'

# Comment this line to restore warnings of experimental DOCA features
add_project_arguments('-D DOCA_ALLOW_EXPERIMENTAL_API', language: ['c', 'cpp'])

sample_dependencies = []
# Required for all DOCA programs
# sample_dependencies += dependency('doca')
sample_dependencies += dependency('doca-regex')
sample_dependencies += dependency('doca-common')
sample_dependencies += dependency('doca-argp')
sample_dependencies += dependency('doca-dma')


# 3rd Party dependencies
# None

sample_srcs = [
	# The sample itself
	SAMPLE_NAME + '_test.c',
	# Main function for the sample's executable
	SAMPLE_NAME + '_main.c',
	# Common code for all DOCA samples
	'common.c',
	# Common code for all DOCA applications
	'utils.c',
]

sample_inc_dirs  = ['./']
# # Common DOCA logic (samples)
# sample_inc_dirs += include_directories('../..')
# # Common DOCA logic
# sample_inc_dirs += include_directories('../../..')
# # Common DOCA logic (applications)
# sample_inc_dirs += include_directories('../../../applications/common/src')

executable('doca_' + SAMPLE_NAME, sample_srcs,
	c_args : '-Wno-missing-braces',
	dependencies : sample_dependencies,
	include_directories: sample_inc_dirs,
	install: false)
