# monitor.py - watch the Homylon engine think: every line it sends, as it happens.
#   python3 monitor.py              (the engine on this computer)
#   python3 monitor.py 192.168.1.10 (the engine on another computer)
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))   # homylon.py is one folder up
import homylon

if len(sys.argv) > 1:
    homylon.ENGINE = sys.argv[1]
PORT = 55263

listener = homylon.Listener(PORT)
print("Watching the engine. Stop with ctrl-C.")
heartbeat = lambda: homylon.register_monitor("pythonmonitor", PORT)   # register again every 3 s
for line, _ in listener.messages(every=3, then=heartbeat):
    print(f'{line.get("monitorMessageType", ""):8} {line.get("monitorMessageText", "")}')
