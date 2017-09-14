#include "utilities.h"
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

void timespec_positive_diff(struct timespec *start, struct timespec *stop, struct timespec *result) {
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


int timespec_diff(struct timespec *start, struct timespec *stop, struct timespec *result) {
	int sign = 1;
	if (stop->tv_sec > start->tv_sec) {
		timespec_positive_diff(start, stop, result);
	}
	else if (stop->tv_sec < start->tv_sec) {
		timespec_positive_diff(stop, start, result);
		sign = -1;
	}
	else if (stop->tv_nsec >= start->tv_nsec) {
		timespec_positive_diff(start, stop, result);
	}
	else {
		timespec_positive_diff(stop, start, result);
		sign = -1;
	}
	if (result->tv_sec == 0 && result->tv_nsec == 0)
		sign = 0;
	return sign;
}

int get_mem_info(pid_t pid, uint64_t *mem_byte, uint64_t *vmem_byte) {
	statm_info m_info;
	char statm_filename[1024], statm_content[2048];
	FILE *statm_fp;
	long page_size = sysconf(_SC_PAGESIZE);

	sprintf(statm_filename, "/proc/%u/statm", (unsigned) pid);

	if ((statm_fp = fopen(statm_filename, "r")) == NULL) {
		return -1;
	}

	if (fgets(statm_content, 2048, statm_fp) == NULL) {
		fclose(statm_fp);
		return -1;
	}

	sscanf(statm_content, "%u %u %u %u %u %u %u", &(m_info.size), &(m_info.resident), &(m_info.shared),
		&(m_info.text), &(m_info.lib), &(m_info.data), &(m_info.dt));

	fclose(statm_fp);

	*mem_byte = m_info.resident * page_size;
	*vmem_byte = m_info.size * page_size;

	return 0;
}

int get_proc_info(pid_t pid, stat_info *pinfo) {
	char stat_filename[1024], stat_content[2048];
	char *p_start, *p_end;
	FILE *stat_fp;

	sprintf(stat_filename, "/proc/%u/stat", (unsigned) pid);

	if ((stat_fp = fopen(stat_filename, "r")) == NULL) {
		return (pinfo->pid = -1);
	}

	if (fgets(stat_content, 2048, stat_fp) == NULL) {
		fclose(stat_fp);
		return (pinfo->pid = -1);
	}

	sscanf(stat_content, "%u", &(pinfo->pid));

	p_start = strchr(stat_content, '(') + 1;
	p_end = strchr(stat_content, ')');
	strncpy(pinfo->exName, p_start, p_end - p_start);
	pinfo->exName[p_end - p_start] = '\0';

	sscanf(p_end + 2, "%c %d %d %d %d %d %u %u %u %u %u %d %d %d %d %d %d %u %u %d %u %u %u %u %u %u %u %u %d %d %d %d %u",
		&(pinfo->state), &(pinfo->ppid), &(pinfo->pgrp), &(pinfo->session),
		&(pinfo->tty), &(pinfo->tpgid), &(pinfo->flags), &(pinfo->minflt),
		&(pinfo->cminflt), &(pinfo->majflt), &(pinfo->cmajflt),
		&(pinfo->utime), &(pinfo->stime), &(pinfo->cutime),
		&(pinfo->cstime), &(pinfo->counter), &(pinfo->priority),
		&(pinfo->timeout), &(pinfo->itrealvalue), &(pinfo->starttime),
		&(pinfo->vsize), &(pinfo->rss), &(pinfo->rlim), &(pinfo->startcode),
		&(pinfo->endcode), &(pinfo->startstack), &(pinfo->kstkesp),
		&(pinfo->kstkeip), &(pinfo->signal), &(pinfo->blocked),
		&(pinfo->sigignore), &(pinfo->sigcatch), &(pinfo->wchan));

	fclose(stat_fp);
	return 0;
}

double get_cpu_perc(const stat_info *s1, const stat_info *s2, const struct timespec *interval) {
	long clock_ticks = sysconf(_SC_CLK_TCK);
	int total1 = s1->utime + s1->stime + s1->cutime + s1->cstime;
	int total2 = s2->utime + s2->stime + s2->cutime + s2->cstime;
	return 100 * (total2 - total1) / (double)clock_ticks / (interval->tv_sec + interval->tv_nsec / 1.0e9);
}
