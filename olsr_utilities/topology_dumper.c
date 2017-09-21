#include "socket.h"
#include "utilities.h"
#include <inttypes.h>

#define HOST "127.0.0.1"
#define PORT 2009
#define PORT_V1 9090
#define POP_PORT 1234
#define REQ_TOPOLOGY "/netjsoninfo filter graph ipv4_0/quit\n"
#define REQ_TOPOLOGY_V1 "/topology\n"
#define REQ_ROUTE "/netjsoninfo filter route ipv4_0/quit\n"
#define REQ_ROUTE_V1 "/routes\n"
#define REQ_HELLO "/config get interface.hello_interval/quit\n"
#define REQ_HELLO_V1 "/HelloTimer\n"
#define REQ_TC "/config get olsrv2.tc_interval/quit\n"
#define REQ_TC_V1 "/TcTimer\n"
#define EXT_TOPO ".topo"
#define EXT_ROUTE ".route"
#define EXT_INTERVAL ".int"
#define EXT_PERF ".perf"

char* get_olsr_data(const char *query, int port)
{
	int sd, sent;
	char *recv_buffer = 0;
	if((sd = _create_socket(HOST, port))==0){
		goto exit_err;
	}
	if( (sent = send(sd, query, strlen(query), MSG_NOSIGNAL))==-1){
		close(sd);
		goto exit_err;
	}
	if(!_telnet_receive(sd, &recv_buffer)){
		close(sd);
		goto exit_err;
	}
	close(sd);
	return recv_buffer;

	exit_err:
	recv_buffer = malloc(1);
	if (recv_buffer)
		recv_buffer[0] = 0;
	return recv_buffer;
}

void remove_newline(char *str) {
	if (!str || strcmp(str, "") == 0)
		return;
	int pos = 0;
	while (str[pos] != 0 && str[pos] != '\n')
		pos++;
	if (str[pos] == 0)
		return;
	for (int i = pos; i < strlen(str); i++)
		str[i] = str[i+1];
}

int compare(const char *s1, const char *s2, const char *tag) {
	if (tag == 0)
		return strcmp(s1, s2);
	char *tag1 = strstr(s1, tag);
	char *tag2 = strstr(s2, tag);
	return strcmp(tag1, tag2);
}

int main(int argc, char **argv) {

	char *topology, *routing_table, *hello, *tc;
	char *last_topology, *last_routing_table, *last_hello, *last_tc;
	struct timespec start_time;
	struct timespec stop_time;
	struct timespec interval;
	struct timespec next;
	struct timespec wait_time;
	struct timespec now;
	struct timespec till_end;
	struct timespec last_cpu_meas, cpu_meas, cpu_time;
	FILE *topo_out, *route_out, *interval_out, *perf_out;
	char base_filename[1024], topo_filename[1024], route_filename[1024], interval_filename[1024], perf_filename[1024];
	uint64_t argv_start_time, argv_stop_time, argv_interval;
	char *argv_id;
	int i;
	pid_t olsr_pid, prince_pid;
	stat_info olsr_info1, olsr_info2, prince_info1, prince_info2;
	double olsr_cpu, prince_cpu;
	uint64_t olsr_mem, olsr_vmem, prince_mem, prince_vmem;
	int olsr_version;

	if (argc != 8) {
		printf("Usage: %s <start time in unix time> <stop time in unix time> <interval in ms> <output prefix> <olsr pid> <prince pid> <olsr version (1 or 2)>\n", argv[0]);
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

	sscanf(argv[5], "%" SCNd32, &olsr_pid);
	sscanf(argv[6], "%" SCNd32, &prince_pid);

	sscanf(argv[7], "%" SCNd32, &olsr_version);

	next = start_time;

	char *rq_topo = olsr_version == 1 ? REQ_TOPOLOGY_V1 : REQ_TOPOLOGY;
	char *rq_route = olsr_version == 1 ? REQ_ROUTE_V1 : REQ_ROUTE;
	char *rq_hello = olsr_version == 1 ? REQ_HELLO_V1 : REQ_HELLO;
	char *rq_tc = olsr_version == 1 ? REQ_TC_V1 : REQ_TC;
	int port = olsr_version == 1 ? PORT_V1 : PORT;
	int pop_port = olsr_version == 1 ? POP_PORT : PORT;

	i = 0;
	last_topology = 0;
	last_routing_table = 0;
	last_hello = 0;
	last_tc = 0;
	prince_mem = 0;
	prince_vmem = 0;
	prince_cpu = 0;
	olsr_cpu = 0;
	int sign;
	do {
		timespec_get(&now, TIME_UTC);
		sign = timespec_diff(&now, &next, &wait_time);
		if (sign > 0)
			nanosleep(&wait_time, 0);
		else
			next = now;
		topology = get_olsr_data(rq_topo, port);
		routing_table = get_olsr_data(rq_route, port);
		hello = get_olsr_data(rq_hello, pop_port);
		if (olsr_version == 2)
			remove_newline(hello);
		tc = get_olsr_data(rq_tc, pop_port);
		if (olsr_version == 2)
			remove_newline(tc);

		get_mem_info(olsr_pid, &olsr_mem, &olsr_vmem);
		get_proc_info(olsr_pid, &olsr_info2);
		if (prince_pid != 0) {
			get_mem_info(prince_pid, &prince_mem, &prince_vmem);
			get_proc_info(prince_pid, &prince_info2);
		}
		timespec_get(&cpu_meas, TIME_UTC);

		if (i != 0) {
			timespec_diff(&last_cpu_meas, &cpu_meas, &cpu_time);
			olsr_cpu = get_cpu_perc(&olsr_info1, &olsr_info2, &cpu_time);
			if (prince_pid != 0) {
				prince_cpu = get_cpu_perc(&prince_info1, &prince_info2, &cpu_time);
			}
		}
		olsr_info1 = olsr_info2;
		prince_info1 = prince_info2;
		last_cpu_meas = cpu_meas;

		timespec_get(&now, TIME_UTC);
		sprintf(base_filename, "%s_%06d_%lld_%09lld", argv_id, i, (long long)now.tv_sec, (long long)now.tv_nsec);
		if (topology && (!last_topology || compare(last_topology, topology, olsr_version == 1 ? "\"topology\"" : 0) != 0)) {
			sprintf(topo_filename, "%s%s", base_filename, EXT_TOPO);
			topo_out = fopen(topo_filename, "w");
			fprintf(topo_out, "%s", topology);
			free(last_topology);
			last_topology = topology;
			fclose(topo_out);
		}
		else {
			free(topology);
		}
		if (routing_table && (!last_routing_table || compare(last_routing_table, routing_table, olsr_version == 1 ? "\"routes\"" : 0) != 0)) {
			sprintf(route_filename, "%s%s", base_filename, EXT_ROUTE);
			route_out = fopen(route_filename, "w");
			fprintf(route_out, "%s", routing_table);
			free(last_routing_table);
			last_routing_table = routing_table;
			fclose(route_out);
		}
		else {
			free(routing_table);
		}
		if (hello && tc && (!last_hello || strcmp(last_hello, hello) != 0 || strcmp(last_tc, tc) != 0)) {
			sprintf(interval_filename, "%s%s", base_filename, EXT_INTERVAL);
			interval_out = fopen(interval_filename, "w");
			fprintf(interval_out, "%s", hello);
			fprintf(interval_out, "%s", tc);
			free(last_hello);
			last_hello = hello;
			free(last_tc);
			last_tc = tc;
			fclose(interval_out);
		}
		else {
			free(hello);
			free(tc);
		}

		sprintf(perf_filename, "%s%s", base_filename, EXT_PERF);
		perf_out = fopen(perf_filename, "w");
		fprintf(perf_out, "%lf %lu %lu\n", olsr_cpu, olsr_mem, olsr_vmem);
		fprintf(perf_out, "%lf %lu %lu\n", prince_cpu, prince_mem, prince_vmem);
		fclose(perf_out);

		i++;
		timespec_sum(&next, &interval, &next);
		sign = timespec_diff(&next, &stop_time, &till_end);
	} while (sign >= 0);


	free(last_topology);
	free(last_routing_table);
	free(last_hello);
	free(last_tc);

	return 0;
}
