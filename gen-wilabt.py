header = """<?xml version='1.0'?>
<rspec xmlns="http://www.geni.net/resources/rspec/3" type="request" \
generated_by="jFed RSpec Editor" generated="2017-04-11T14:27:13.049+02:00" \
xmlns:emulab="http://www.protogeni.net/resources/rspec/ext/emulab/1" \
xmlns:delay="http://www.protogeni.net/resources/rspec/ext/delay/1" \
xmlns:jfed-command="http://jfed.iminds.be/rspec/ext/jfed-command/1" \
xmlns:client="http://www.protogeni.net/resources/rspec/ext/client/1" \
xmlns:jfed-ssh-keys="http://jfed.iminds.be/rspec/ext/jfed-ssh-keys/1" \
xmlns:jfed="http://jfed.iminds.be/rspec/ext/jfed/1" \
xmlns:sharedvlan="http://www.protogeni.net/resources/rspec/ext/shared-vlan/1" \
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
xsi:schemaLocation="http://www.geni.net/resources/rspec/3 \
http://www.geni.net/resources/rspec/3/request.xsd ">"""

footer = """</rspec>"""

node_template = """<node client_id="nuc0-%d" exclusive="true" \
  component_manager_id="urn:publicid:IDN+wilab1.ilabt.iminds.be+authority+cm" \
  component_id="urn:publicid:IDN+wilab1.ilabt.iminds.be+node+nuc0-%d">
  <sliver_type name="raw-pc"/>
  <location xmlns="http://jfed.iminds.be/rspec/ext/jfed/1" x="%f" y="%f"/>
</node>"""

h = 40
w = 120
x = 100
y = 100

print header
for i in range(1, 45):
    row = (i - 1) / 11
    col = (i - 1) % 11
    print node_template % (i, i, x + col * w, y + row * h)
print footer