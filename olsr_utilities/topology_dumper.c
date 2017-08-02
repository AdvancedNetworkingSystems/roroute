#include "socket.h"
#include "utilities.h"
#include <inttypes.h>

#define HOST "127.0.0.1"
#define PORT 2009
#define REQ_TOPOLOGY "/netjsoninfo filter graph ipv4_0/quit\n"
#define REQ_ROUTE "/netjsoninfo filter route ipv4_0/quit\n"
#define REQ_HELLO "/config get interface.hello_interval/quit\n"
#define REQ_TC "/config get olsrv2.tc_interval/quit\n"
#define EXT_TOPO ".topo"
#define EXT_ROUTE ".route"
#define EXT_INTERVAL ".int"

char* get_olsr_data(const char *query)
{
	int sd, sent;
	char *recv_buffer;
	if((sd = _create_socket(HOST, PORT))==0){
		return 0;
	}
	if( (sent = send(sd, query, strlen(query), MSG_NOSIGNAL))==-1){
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

void remove_newline(char *str) {
	int pos = 0;
	while (str[pos] != 0 && str[pos] != '\n')
		pos++;
	if (str[pos] == 0)
		return;
	for (int i = pos; i < strlen(str); i++)
		str[i] = str[i+1];
}

int main(int argc, char **argv) {

	char *topology, *routing_table, *hello, *tc;
	struct timespec start_time;
	struct timespec stop_time;
	struct timespec interval;
	struct timespec next;
	struct timespec wait_time;
	struct timespec now;
	struct timespec till_end;
	FILE *topo_out, *route_out, *interval_out;
	char base_filename[1024], topo_filename[1024], route_filename[1024], interval_filename[1024];
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
		topology = get_olsr_data(REQ_TOPOLOGY);
		routing_table = get_olsr_data(REQ_ROUTE);
		hello = get_olsr_data(REQ_HELLO);
		remove_newline(hello);
		tc = get_olsr_data(REQ_TC);
		remove_newline(tc);

		timespec_get(&now, TIME_UTC);
		sprintf(base_filename, "%s_%06d_%lld_%09lld", argv_id, i, (long long)now.tv_sec, (long long)now.tv_nsec);
		sprintf(topo_filename, "%s%s", base_filename, EXT_TOPO);
		sprintf(route_filename, "%s%s", base_filename, EXT_ROUTE);
		sprintf(interval_filename, "%s%s", base_filename, EXT_INTERVAL);
		topo_out = fopen(topo_filename, "w");
		route_out = fopen(route_filename, "w");
		interval_out = fopen(interval_filename, "w");
		if (topology) {
			fprintf(topo_out, "%s", topology);
			free(topology);
		}
		if (routing_table) {
			fprintf(route_out, "%s", routing_table);
			free(routing_table);
		}
		if (hello) {
			fprintf(interval_out, "%s", hello);
			free(hello);
		}
		if (tc) {
			fprintf(interval_out, "%s", tc);
			free(tc);
		}
		fclose(topo_out);
		fclose(route_out);
		fclose(interval_out);
		i++;
		timespec_sum(&next, &interval, &next);
		timespec_diff(&next, &stop_time, &till_end);
	} while (till_end.tv_sec >= 0);

	return 0;
}
