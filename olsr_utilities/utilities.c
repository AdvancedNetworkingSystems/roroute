#include "utilities.h"

void timespec_diff(struct timespec *start, struct timespec *stop, struct timespec *result) {
	if ((stop->tv_nsec - start->tv_nsec) < 0) {
		result->tv_sec = stop->tv_sec - start->tv_sec - 1;
		result->tv_nsec = stop->tv_nsec - start->tv_nsec + 1000000000;
	} else {
		result->tv_sec = stop->tv_sec - start->tv_sec;
		result->tv_nsec = stop->tv_nsec - start->tv_nsec;
	}
}

void timespec_sum(struct timespec *a, struct timespec *b, struct timespec *result) {
	//use a temporary variable so we can do the sum in place
	struct timespec tmp;
	tmp.tv_nsec = a->tv_nsec + b->tv_nsec;
	tmp.tv_sec = a->tv_sec + b->tv_sec;
	if (tmp.tv_nsec >= 1000000000) {
		tmp.tv_sec++;
		tmp.tv_nsec -= 1000000000;
	}
	*result = tmp;
}

