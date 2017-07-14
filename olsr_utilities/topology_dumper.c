#include "socket.h"
#include "utilities.h"
#include <inttypes.h>

#define HOST "127.0.0.1"
#define PORT 2009
#define REQ "/netjsoninfo filter graph ipv4_0/quit\n"

/**
 * Get the topology data from host
 * @param oonf plugin handler object
 * @return 1 if success, 0 otherwise
 */
char* get_topology()
{
	int sd, sent;
	char *recv_buffer;
	if((sd = _create_socket(HOST, PORT))==0){
		return 0;
	}
	if( (sent = send(sd, REQ, strlen(REQ), MSG_NOSIGNAL))==-1){
		close(sd);
		return 0;
	}
	if(!_telnet_receive(sd, &recv_buffer)){
		close(sd);
		return 0;
	}
	close(sd);
	return recv_buffer;
}

int main(int argc, char **argv) {

	char *topology;
	struct timespec start_time;
	struct timespec stop_time;
	struct timespec interval;
	struct timespec next;
	struct timespec wait_time;
	struct timespec now;
	struct timespec till_end;
	FILE *out;
	char filename[1024];
	uint64_t argv_start_time, argv_stop_time, argv_interval;
	char *argv_id;
	int i;

	if (argc != 5) {
		printf("Usage: %s <start time in unix time> <stop time in unix time> <interval in ms> <output prefix>\n", argv[0]);
		exit(1);
	}

	sscanf(argv[1], "%" SCNu64, &argv_start_time);
	start_time.tv_sec = argv_start_time;
	start_time.tv_nsec = 0;

	sscanf(argv[2], "%" SCNu64, &argv_stop_time);
	stop_time.tv_sec = argv_stop_time;
	stop_time.tv_nsec = 0;

	sscanf(argv[3], "%" SCNu64, &argv_interval);
	interval.tv_sec = argv_interval / 1000;
	interval.tv_nsec = argv_interval % 1000 * 1000000;

	argv_id = argv[4];

	next = start_time;

	i = 0;
	do {
		timespec_get(&now, TIME_UTC);
		timespec_diff(&now, &next, &wait_time);
		nanosleep(&wait_time, 0);
		topology = get_topology();
		timespec_get(&now, TIME_UTC);
		sprintf(filename, "%s_%06d_%lld_%09lld", argv_id, i, (long long)now.tv_sec, (long long)now.tv_nsec);
		out = fopen(filename, "w");
		if (topology) {
			fprintf(out, "%s", topology);
			free(topology);
		}
		fclose(out);
		i++;
		timespec_sum(&next, &interval, &next);
		timespec_diff(&next, &stop_time, &till_end);
	} while (till_end.tv_sec >= 0);

	return 0;
}
