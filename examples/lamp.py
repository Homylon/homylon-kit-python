# lamp.py - a Homylon agent: a lamp that lives in your terminal.
#   python3 lamp.py
# In a scene:  light pylamp on FF0000 brightness 80
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))   # homylon.py is one folder up
import homylon

PORT = 55301
lamp = {"on": False, "brightness": 100, "color": "FFD8A0"}

def announce():
    homylon.announce("pyagent", "lights", [{"name": "pylamp", "type": "colorLight", "state": lamp}], PORT)

listener = homylon.Listener(PORT)
announce()
print("The lamp is waiting. Stop with ctrl-C.")
for message, sender in listener.messages():
    if homylon.action(message) == "changelightstate":
        if "onOff" in message: lamp["on"] = message["onOff"] == "on"
        if "brightness" in message: lamp["brightness"] = int(float(message["brightness"]))
        if "color" in message: lamp["color"] = message["color"].upper()
        r, g, b = (int(lamp["color"][i:i + 2], 16) * lamp["brightness"] // 100 for i in (0, 2, 4))
        print(f"\033[48;2;{r};{g};{b}m        \033[0m" if lamp["on"] else "(off)")
        homylon.changed_light("pylamp", lamp["on"], lamp["brightness"], lamp["color"], message.get("requestID"))
    elif homylon.engine_asked(message, sender):   # the engine (re)started: introduce ourselves again
        announce()
    elif homylon.refused(message):
        print("This engine does not want this agent.")
