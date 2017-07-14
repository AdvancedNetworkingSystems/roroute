all: topology_dumper runat

runat: utilities.o runat.o
	$(CC) -o $@ $^

topology_dumper: socket.o topology_dumper.o utilities.o
	$(CC) -o $@ $^

%.o: %.c socket.h utilities.h
	$(CC) -c -o $@ $<

.PHONY: clean

clean:
	rm -f *.o topology_dumper runat
