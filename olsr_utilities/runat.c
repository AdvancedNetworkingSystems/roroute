#include "utilities.h"
#include <inttypes.h>
#include <stdlib.h>
#include <stdio.h>

int main(int argc, char **argv) {

	struct timespec start_time;
	struct timespec wait_time;
	struct timespec now;
	uint64_t argv_start_time;
	uint64_t argv_start_milliseconds;
	char *argv_command;

	if (argc != 4) {
		printf("Usage: %s <start time in unix time (seconds)> <milliseconds> <command>\n", argv[0]);
		exit(1);
	}

	sscanf(argv[1], "%" SCNu64, &argv_start_time);
	sscanf(argv[2], "%" SCNu64, &argv_start_milliseconds);
	start_time.tv_sec = argv_start_time;
	start_time.tv_nsec = argv_start_milliseconds * 1000000;
	printf("%lld %lu\n", (long long int)start_time.tv_sec, argv_start_milliseconds);

	argv_command = argv[3];

	timespec_get(&now, TIME_UTC);
	timespec_diff(&now, &start_time, &wait_time);
	nanosleep(&wait_time, 0);
	return system(argv_command);
}
