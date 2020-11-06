/* -*- P4_16 -*- */
#ifndef PORT_AUTHORIZER_P4_NZJ90FQY
#define PORT_AUTHORIZER_P4_NZJ90FQY

control PortAuthorizer(
		in bit<9> port,
		in macAddr_t mac,
		out bool authorized
	) {

	action grant_access() {
		authorized = true;
	}

	action deny_access() {
		authorized = false;
	}

	table auto_authorizations {
		key = {
			port: exact;
			mac: exact;
		}

		actions = {
			grant_access;
			deny_access;
		}

		default_action = deny_access;
	}

	table forced_authorizations {
		key = {
			port: exact;
		}

		actions = {
			grant_access;
			NoAction;
		}

		default_action = NoAction;
	}

	table forced_unauthorizations {
		key = {
			port: exact;
		}

		actions = {
			deny_access;
			NoAction;
		}

		default_action = NoAction;
	}

	apply {
		authorized = false;

		if(forced_unauthorizations.apply().hit) {
			return;
		}

		if(!forced_authorizations.apply().hit) {
			auto_authorizations.apply();
		}
	}
}

#endif /* end of include guard: PORT_AUTHORIZER_P4_NZJ90FQY */
