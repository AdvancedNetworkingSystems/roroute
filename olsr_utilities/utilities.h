#ifndef UTILITIES_H_
#define UTILITIES_H_

#include <time.h>
#include <inttypes.h>

/**
 * Struct representing info inside /proc/[pid]/stat
 */
typedef struct statstruct_proc {
	int pid;
	char exName[1024];
	char state;
	unsigned euid, egid;
	int ppid;
	int pgrp;
	int session;
	int tty;
	int tpgid;
	unsigned int flags;
	unsigned int minflt;
	unsigned int cminflt;
	unsigned int majflt;
	unsigned int cmajflt;
	int utime;
	int stime;
	int cutime;
	int cstime;
	int counter;
	int priority;
	unsigned int timeout;
	unsigned int itrealvalue;
	int starttime;
	unsigned int vsize;
	unsigned int rss;
	unsigned int rlim;
	unsigned int startcode;
	unsigned int endcode;
	unsigned int startstack;
	unsigned int kstkesp;
	unsigned int kstkeip;
	int signal;
	int blocked;
	int sigignore;
	int sigcatch;
	unsigned int wchan;
	int sched, sched_priority;
} stat_info;

/**
 * Struct representing info inside /proc/[pid]/statm
 */
typedef struct statstruct_proc_statm {
	unsigned int size;
	unsigned int resident;
	unsigned int shared;
	unsigned int text;
	unsigned int lib;
	unsigned int data;
	unsigned int dt;
} statm_info;

int timespec_diff(struct timespec *start, struct timespec *stop, struct timespec *result);
void timespec_sum(struct timespec *a, struct timespec *b, struct timespec *result);
int get_mem_info(pid_t pid, uint64_t *mem_byte, uint64_t *vmem_byte);
int get_proc_info(pid_t pid, stat_info *pinfo);
double get_cpu_perc(const stat_info *s1, const stat_info *s2, const struct timespec *interval);

#endif
