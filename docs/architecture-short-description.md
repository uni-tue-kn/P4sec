# General

- 3-tier Architecture
	- WAN controller
		- Manages Sites (IPsec connections)
		- Is accessible from the outside
	- Global controller
		- Manages one site
		- Knows the site topology
		- Creates MACsec connections
		- Notifies the WAN controller if changes happen (e.g. concentrator, new subnet etc.)
		- Manages routes of the site
	- Local controller
		- Sends LLDP / BDDP packets
		- Knows local topology of switch (ports)
		- Writes / Reads table entries
		- Notifies global controller on changes (e.g. timeouts)
		- Is master of one switch

# Site-to-Site

- Connect two sites with each other via IPsec tunnel

