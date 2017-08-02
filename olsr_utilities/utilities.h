#ifndef UTILITIES_H_
#define UTILITIES_H_

#include <time.h>

int timespec_diff(struct timespec *start, struct timespec *stop, struct timespec *result);
void timespec_sum(struct timespec *a, struct timespec *b, struct timespec *result);

#endif
