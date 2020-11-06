# common
from common_lib.event import EventSystem
from common_lib.logger import Logger

# client
from client_lib.settings import Settings

# other
from typing import Set, Callable
from scapy.all import sniff # type: ignore
from scapy.layers.dns import DNS # type: ignore
from ipaddress import ip_address
from threading import Thread, Event
from dns.resolver import query # type: ignore

DNSRequestHandler = Callable

class DNSInterceptor:

    def __init__(self, logger: Logger, settings: Settings, event_system: EventSystem) -> None:
        self._logger = logger
        self._event_system = event_system
        self._dns_request_handlers = set() # type: Set[ DNSRequestHandler ]
        self._dns_ip = ip_address("127.0.0.1")
        self._interface = "lo"
        self._domains = set([ "dns-test.p4-vpn.haeberle.me" ])
        self._thread = Thread(target=self._sniff);
        self._teardown = Event()

    def on_dns_request(self, handler: DNSRequestHandler) -> None:
        self._dns_request_handlers.add(handler)

    def _handle_dns_request(self, request) -> None:
        for handler in self._dns_request_handlers:
            try:
                handler(request)
            except Exception as e:
                self._logger.error(str(e))

    def _check_dns_packet(self, packet: DNS) -> None:
        try:
            if DNS in packet and packet[DNS].opcode == 0:
                for domain in self._domains:
                    # filter by domain name and qtype (A record)
                    if domain in str(packet["DNS Question Record"].qname) and packet["DNS Question Record"].qtype == 1:
                        target = str(packet["DNS Question Record"].qname, "utf-8")
                        txt_record = self._get_txt_record(target)
                        if self._check_if_tunneled(txt_record):
                            self._event_system.acquire()
                            self._handle_dns_request(target)
                            self._event_system.release()
        except Exception as e:
            self._logger.error("DNS error: " + str(e))


    def _get_txt_record(self, domain):
        self._logger.info("getting txt record for " + domain)
        answer = query(domain, "txt")

        # check if the answer contains a resource record with type txt (16)
        return str(answer[0]).strip("\"")

    def _check_if_tunneled(self, record):
        if record.startswith("CISCO-CLS="):
            record_items = {key: value for [key, value] in [x.split(":") for x in record[10:].split("|")]}
            if record_items["tunneled"] and record_items["tunneled"] == "yes":
                return True
        return False

    def _sniff(self) -> None:
        self._logger.info("Sniffing on " + str(self._interface))
        dns_filter = "udp and port 53 and ip dst {0}".format(str(self._dns_ip))
        while not self._teardown.is_set():
            sniff(iface=self._interface, filter=dns_filter, \
                    prn=self._check_dns_packet, store=0, count=1, timeout=1)

    def start_sniffing(self) -> None:
        self._teardown.clear()
        self._thread.start()

    def stop_sniffing(self) -> None:
        self._teardown.set()
        self._thread.join()
