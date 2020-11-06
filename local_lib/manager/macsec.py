# common
from common_lib.logger import Logger
from common_lib.macsec import Rule, Address, Channel
from common_lib.event import EventSystem, Task

# local
from local_lib.manager.port_authorizer import PortAuthorizer
from local_lib.manager.topology import TopologyManager
from local_lib.p4runtime_lib import SwitchConnection
from local_lib.packet import CPUPacket, Config, Notification
from local_lib.global_ import GlobalController
from local_lib.settings import Settings

# other
from typing import Dict, Set
import traceback
from time import sleep
from datetime import datetime, timedelta
from os import urandom
from macsec_pb2 import bddp_key # type: ignore

class MacsecManager:
    class KeyState:
        KEY1 = 0
        KEY2 = 1

    def __init__(self,
            logger: Logger,
            settings: Settings,
            switch_connection: SwitchConnection,
            port_authorizer: PortAuthorizer,
            global_controller: GlobalController,
            event_system: EventSystem,
            topology_manager: TopologyManager
        ) -> None:
        self._logger = logger
        self._settings = settings
        self._switch_connection = switch_connection
        self._port_authorizer = port_authorizer
        self._global_controller = global_controller
        self._event_system = event_system
        self._topology_manager = topology_manager

        self._rules = dict() # type: Dict[ str, Rule ]
        self._unused_registers = set(range(255)) # type: Set[ int ]
        self._registers = dict() # type: Dict[ str, int ]
        self._register_to_rules = dict() # type: Dict[ int, Rule ]

        self._soft_time_limit_timeouts = dict() # type: Dict[ str, Task ]
        self._key_state = dict() # type: Dict[ str, int ]

    def _get_register(self) -> int:
        return self._unused_registers.pop()

    def _return_register(self, register: int) -> None:
        self._unused_registers.add(register)

    def _reset_counter(self, index: int) -> None:
        cpu = CPUPacket(reason="CONFIG")
        config = Config(type="MACSEC_RESET_COUNTER", index=index, value=0)
        self._switch_connection.send_packet_out(bytes(cpu / config))

    def _set_soft_packet_limit(self, index: int, value: int) -> None:
        self._logger.debug("Set soft packet limit " + str(value) + " for " + str(index))
        cpu = CPUPacket(reason="CONFIG")
        config = Config(type="MACSEC_SET_SOFT_PACKET_LIMIT", index=index, value=value)
        self._switch_connection.send_packet_out(bytes(cpu / config))

    def _set_hard_packet_limit(self, index: int, value: int) -> None:
        self._logger.debug("Set hard packet limit " + str(value) + " for " + str(index))
        cpu = CPUPacket(reason="CONFIG")
        config = Config(type="MACSEC_SET_HARD_PACKET_LIMIT", index=index, value=value)
        self._switch_connection.send_packet_out(bytes(cpu / config))

    def _set_soft_time_limit(self, rule: Rule) -> None:
        if str(rule.get_protect().get_address()) in self._soft_time_limit_timeouts:
            # task already exists -> reschedule
            task = self._soft_time_limit_timeouts[str(rule.get_protect().get_address())]
            task.set_ready(datetime.timestamp(rule.get_soft_time_limit()))
            return

        def handle_soft_time_limit():
            del self._soft_time_limit_timeouts[str(rule.get_protect().get_address())]
            macsec = self._global_controller.get_service("macsec")
            # the global controller will trigger the write command -> release the lock
            self._event_system.release()
            macsec.notify_soft_time_limit(rule.get_edge())
            self._event_system.acquire()

        task = self._event_system.set_timeout(
            handle_soft_time_limit,
            int((rule.get_soft_time_limit() - datetime.now()).total_seconds())
        )
        self._soft_time_limit_timeouts[str(rule.get_protect().get_address())] = task

    def add(self, rule: Rule, stop=False) -> None:
        try:
            self._logger.info("add MACsec rule: " + str(rule))

            #protect rule
            protect = rule.get_protect()
            register = self._get_register()
            self._registers[str(protect.get_address())] = register

            self._reset_counter(register)
            self._set_soft_packet_limit(register, rule.get_soft_packet_limit());
            self._set_hard_packet_limit(register, rule.get_hard_packet_limit());
            self._set_soft_time_limit(rule)

            self._switch_connection.write(
                table_name="ingress.ethernet.macsec_protect.targets",
                match_fields={
                    "standard_metadata.egress_spec": protect.get_address().get_port()
                },
                action_name="ingress.ethernet.macsec_protect.protect_packet",
                action_params={
                    "key1": protect.get_key(),
                    "key2": urandom(16), #simulate old key
                    "system_id": self._settings.get_mac(),
                    "register_index": register
                }
            )

            #validate rule
            validate = rule.get_validate()
            self._switch_connection.write(
                table_name="ingress.ethernet.macsec_validate.sources",
                match_fields={
                    "standard_metadata.ingress_port": validate.get_address().get_port()
                },
                action_name="ingress.ethernet.macsec_validate.validate_packet",
                action_params={
                    "key1": validate.get_key(),
                    "key2": urandom(16), #simulate old key
                    "register_index": register
                }
            )
            self._port_authorizer.force_authorization(protect.get_address().get_port())
            self._rules[str(rule.get_protect().get_address())] = rule
            self._register_to_rules[register] = rule
            self._key_state[str(rule.get_protect().get_address())] = MacsecManager.KeyState.KEY1
        except:
            self._logger.error("Could not write macsec: " + str(rule))
            self.remove(rule.get_protect().get_address())
            # implicit -> self.remove(rule.get_validate().get_address())
            # retry
            if not stop:
                self.add(rule, stop=True)


    def remove(self, address: Address) -> None:
        try:
            self._logger.info("remove MACsec rule: " + str(address))

            self._port_authorizer.unforce_authorization(address.get_port())

            self._switch_connection.delete("ingress.ethernet.macsec_protect.targets",
                match_fields={
                    "standard_metadata.egress_spec": address.get_port()
                }
            )
            self._switch_connection.delete("ingress.ethernet.macsec_validate.sources",
                match_fields={
                    "standard_metadata.ingress_port": address.get_port()
                }
            )
            del self._register_to_rules[self._registers[str(address)]]
            self._return_register(self._registers[str(address)])
            del self._rules[str(address)]
            del self._key_state[str(address)]
            #TODO del self._soft_time_limit_timeouts[str(address)]
        except Exception as e:
            print(e)
            self._logger.error("Could not remove macsec: " + str(address))

    def renew(self, rule: Rule) -> None:
        self._logger.info("Renew MACsec rule: " + str(rule))

        # update timelimit
        if str(rule.get_protect().get_address()) in self._soft_time_limit_timeouts:
            task = self._soft_time_limit_timeouts[str(rule.get_protect().get_address())]
            task.set_ready(datetime.timestamp(rule.get_soft_time_limit()))

        protect = rule.get_protect()
        register = self._registers[str(protect.get_address())]
        old_rule = self._rules[str(protect.get_address())]

        # toggle key state
        key_state = self._key_state[str(rule.get_protect().get_address())]
        key_state = MacsecManager.KeyState.KEY1 if key_state is MacsecManager.KeyState.KEY2 \
            else MacsecManager.KeyState.KEY2
        self._key_state[str(rule.get_protect().get_address())] = key_state

        key1 = protect.get_key() if key_state is MacsecManager.KeyState.KEY1 else \
                old_rule.get_protect().get_key()
        key2 = protect.get_key() if key_state is MacsecManager.KeyState.KEY2 else \
                old_rule.get_protect().get_key()

        protect_entry = self._switch_connection.helper.buildTableEntry(
            table_name="ingress.ethernet.macsec_protect.targets",
            match_fields={
                "standard_metadata.egress_spec": protect.get_address().get_port()
            },
            action_name="ingress.ethernet.macsec_protect.protect_packet",
            action_params={
                "key1": key1,
                "key2": key2,
                "system_id": self._settings.get_mac(),
                "register_index": register
            }
        )

        #validate rule
        validate = rule.get_validate()
        key1 = validate.get_key() if key_state is MacsecManager.KeyState.KEY1 else \
                old_rule.get_validate().get_key()
        key2 = validate.get_key() if key_state is MacsecManager.KeyState.KEY2 else \
                old_rule.get_validate().get_key()
        validate_entry = self._switch_connection.helper.buildTableEntry(
            table_name="ingress.ethernet.macsec_validate.sources",
            match_fields={
                "standard_metadata.ingress_port": validate.get_address().get_port()
            },
            action_name="ingress.ethernet.macsec_validate.validate_packet",
            action_params={
                "key1": key1,
                "key2": key2,
                "register_index": register
            }
        )

        self._switch_connection.update_table_entries([ protect_entry, validate_entry ])

        self._rules[str(protect.get_address())] = rule
        self._set_soft_packet_limit(register, rule.get_soft_packet_limit());
        self._set_hard_packet_limit(register, rule.get_hard_packet_limit());
        self._set_soft_time_limit(rule)

    def handle_notification(self, cpu: CPUPacket) -> None:
        notification = cpu["Notification"]

        # immediatly send payload of notification back to pipeline
        packet = CPUPacket(reason="SEND")
        packet.payload = notification.payload
        self._switch_connection.send_packet_out(bytes(packet))

        macsec = self._global_controller.get_service("macsec")
        if notification.type == Notification(type="MACSEC_SOFT_PACKET_LIMIT").type:
            rule = self._register_to_rules[notification.index]
            macsec.notify_soft_packet_limit(rule.get_edge())

    def send_bddp_packet(self, key: bddp_key) -> None:
        self._topology_manager.send_lldp_packets(key)
