"""homylon.py - talk to the Homylon engine from Python. One file, standard library only.

Copy this file next to your script and `import homylon`. The protocol in full:
https://github.com/Homylon/homylon-protocol

    import homylon
    homylon.ENGINE = "192.168.1.10"            # where the engine runs (default: this computer)
    homylon.send({"action": "changedvariable", "variable": "rain", "value": 1})

Every message is one JSON object with an "action". Small messages go by UDP (one message per
datagram), big ones by TCP (the length in 4 bytes, then the JSON, then close).
"""
import json
import socket
import struct
import time
import uuid

__version__ = "1.0.2"

ENGINE = "127.0.0.1"   # the engine's address
UDP_PORT = 55051       # the engine's UDP port
TCP_PORT = 55050       # the engine's TCP port
SECURITY_KEY = ""      # the engine's security key, when it has one


def _signed(message):
    message = dict(message, timestamp=int(time.time()))
    if SECURITY_KEY:
        message["securityKey"] = SECURITY_KEY
    return json.dumps(message).encode()


def send(message, to=None, port=None):
    """Send a small message by UDP (the normal way)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(_signed(message), (to or ENGINE, port or UDP_PORT))


def send_tcp(message, to=None, port=None):
    """Send a big message by TCP: the length in 4 bytes (most significant first), then the JSON."""
    data = _signed(message)
    with socket.create_connection((to or ENGINE, port or TCP_PORT), timeout=5) as connection:
        connection.sendall(struct.pack(">I", len(data)) + data)


def action(message):
    """The action of a message, the way the engine compares it: ChangeLightState = changelightstate."""
    return str(message.get("action", "")).lower().replace("-", "").replace("_", "")


def my_address(toward=None):
    """The address of this computer that the engine can reach (nothing is sent to find out)."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect((toward or ENGINE, 9))
        return sock.getsockname()[0]


class Listener:
    """Receives the messages the engine sends to this program, by UDP and TCP on one port.

        listener = homylon.Listener(55300)
        for message, sender in listener.messages():
            print(message)
    """

    def __init__(self, port):
        self.port = port
        self.udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp.bind(("0.0.0.0", port))
        self.tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp.bind(("0.0.0.0", port))
        self.tcp.listen()
        self.udp.settimeout(0.2)
        self.tcp.settimeout(0.2)

    def messages(self, every=None, then=None):
        """Yields (message, sender) forever. With every=3 and then=a function, calls that function
        every 3 seconds too, for a heartbeat."""
        last = 0
        while True:
            if every and time.time() - last >= every:
                then()
                last = time.time()
            try:                                            # a UDP datagram: one message
                data, (sender, _) = self.udp.recvfrom(65535)
                yield json.loads(data), sender
            except (socket.timeout, ValueError):
                pass
            try:                                            # a TCP connection: length + message
                connection, (sender, _) = self.tcp.accept()
                with connection:
                    connection.settimeout(5)
                    size = struct.unpack(">I", _read(connection, 4))[0]
                    yield json.loads(_read(connection, size)), sender
            except (socket.timeout, ValueError, struct.error):
                pass


def _read(connection, size):
    data = b""
    while len(data) < size:
        part = connection.recv(size - len(data))
        if not part:
            break
        data += part
    return data


# Monitors and remotes

def register_monitor(name, port, types="all", heartbeat=3):
    """Ask the engine to send its lines to this program. Call it again every `heartbeat` seconds."""
    send({"action": "registermonitor", "monitor": {
        "name": name, "address": my_address(), "port": port, "protocol": "udp",
        "types": types, "heartbeat": heartbeat}})


SESSION = str(uuid.uuid4())    # new at every start: tells the engine this remote restarted


def register_remote(name, port):
    """Register as a remote; repeat every 3 seconds. The engine sends lists by TCP to `port`."""
    send({"action": "registerremote", "remote": {
        "name": name, "port": port, "protocol": "tcp", "session": SESSION}})


# Agents

def announce(agent, kind, things, port, address=None):
    """Tell the engine who this agent is and what it has. kind: lights, sensors, blinds, appliances
    or groups; things: a list of {"name": ..., "type": ..., "state": {...}}. Goes by TCP."""
    send_tcp({"action": "registeragent", "announcement": {
        "announce": {"agent": agent, "type": kind, "ipaddress": address or my_address(),
                     "ports": [{"networkProtocol": "udp", "port": port}]},
        "list": things}})


def changed_sensor(name, kind, status):
    """A sensor changed: kind is motion, temperature, ...; status a number, or True / False."""
    send({"action": "changedsensor", "name": name, "type": kind, "status": status})


def changed_light(name, on, brightness=None, color=None, request_id=None):
    """A lamp changed. Pass the requestID of the command it answers, so a remote can confirm it."""
    message = {"action": "changedlight", "name": name, "state": "on" if on else "off"}
    if brightness is not None:
        message["brightness"] = brightness
    if color:
        message["color"] = color
    if request_id:
        message["requestID"] = request_id
    send(message)


def changed_remote(remote, control, value):
    """A button, switch or slider: rules react with  when remote REMOTE button CONTROL = VALUE."""
    send({"action": "changedremote", "remote": remote, "control": control, "value": value})


def engine_asked(message, sender):
    """For an agent: True when the message asks for an announcement. The engine that asked is then
    the engine to answer: this sets ENGINE and the ports from what the message says."""
    global ENGINE, TCP_PORT, UDP_PORT
    if action(message) != "requestannouncement":
        return False
    ENGINE = message.get("address") or sender      # behind NAT the sender would be the router
    TCP_PORT = int(message.get("tcpport", TCP_PORT))
    UDP_PORT = int(message.get("udpport", UDP_PORT))
    return True


def refused(message):
    """For an agent: True when this engine's scene does not want it (accept / reject)."""
    return action(message) == "agentrefused"
