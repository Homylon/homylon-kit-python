# homylon.py: the Homylon kit for Python

Talk to the Homylon engine from Python: one file, the standard library only, Python 3.7 or later.

**Homylon** is a home automation language and engine you can read: plain-text scenes that say how a
house should behave. Downloads, the manual and the Homylon engine: **[homylon.org](https://www.homylon.org)**.

## Use

Copy [homylon.py](homylon.py) next to your script:

```python
import homylon

homylon.ENGINE = "192.168.1.10"     # where the engine runs (default: this computer)
homylon.changed_sensor("rainsensor", "water", True)
homylon.send({"action": "changedvariable", "variable": "rain", "value": 1})
```

| | |
|---|---|
| `send(message)`, `send_tcp(message)` | send any message: UDP for small ones, TCP (4-byte length + JSON) for big ones |
| `Listener(port).messages()` | receive what the engine sends to you, by UDP and TCP on one port |
| `register_monitor(name, port)` | get every line the engine reports (repeat every 3 s) |
| `register_remote(name, port)` | be a remote: the engine sends you its lists and changes (repeat every 3 s) |
| `announce(agent, kind, things, port)` | be an agent: tell the engine what you have |
| `changed_sensor`, `changed_light`, `changed_remote` | report a change |
| `engine_asked(message, sender)`, `refused(message)` | for agents: the engine asks who you are, or does not want you |

That is all there is. Read the file: it is short, and the comments explain the protocol where it
does something you would not guess.

## Examples

```sh
cd examples
python3 monitor.py      # watch the engine think
python3 lamp.py         # an agent: a lamp that lives in your terminal
```

With `lamp.py` running, try `light pylamp on FF0000 brightness 80` in a scene. More examples, also
without the kit: [homylon-examples](https://github.com/Homylon/homylon-examples).

## More

- The protocol: [homylon-protocol](https://github.com/Homylon/homylon-protocol)
- The same for Swift: [homylon-kit-swift](https://github.com/Homylon/homylon-kit-swift)

## Licence

MIT, see LICENSE.
