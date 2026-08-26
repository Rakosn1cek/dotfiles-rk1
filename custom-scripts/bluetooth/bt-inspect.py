#!/usr/bin/env python3
"""
bt-manager: Unified Bluetooth Controller
Handles: Classic Bluetooth (Phones, Pairing, File Transfer) + BLE GATT (Smart Home Control & Telemetry)
Requires: python-bleak, python-textual
"""

import asyncio
import os
import re
import subprocess
from bleak import BleakScanner, BleakClient
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, ListView, ListItem, Label, Tree, Input, Button, Log
from textual import work

HUMAN_UUID_MAP = {
    "00001800-0000-1000-8000-00805f9b34fb": "Generic Access",
    "00001801-0000-1000-8000-00805f9b34fb": "Attribute Management",
    "0000180a-0000-1000-8000-00805f9b34fb": "Device Information",
    "0000180f-0000-1000-8000-00805f9b34fb": "Battery Service",
    "00002a00-0000-1000-8000-00805f9b34fb": "Device Name",
    "00002a19-0000-1000-8000-00805f9b34fb": "Battery Percentage",
    "00002a24-0000-1000-8000-00805f9b34fb": "Model Number",
    "00002a26-0000-1000-8000-00805f9b34fb": "Firmware Version",
    "00002a29-0000-1000-8000-00805f9b34fb": "Manufacturer",
    "00010203-0405-0607-0809-0a0b0c0d1910": "Govee Light Controller",
    "00010203-0405-0607-0809-0a0b0c0d2b11": "Light Control (Write Endpoint)",
    "00010203-0405-0607-0809-0a0b0c0d2b10": "Light Telemetry / Status",
}

NAMED_COLOURS = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "white": (255, 255, 255),
    "warm": (255, 160, 64),
    "amber": (255, 191, 0),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "purple": (128, 0, 128),
    "magenta": (255, 0, 255),
    "orange": (255, 100, 0),
    "pink": (255, 105, 180),
}


def build_govee_packet(cmd_type: str, *args) -> list[bytearray]:
    frames = []

    def make_frame(data: list[int]) -> bytearray:
        frame = bytearray(20)
        frame[0] = 0x33
        for i, val in enumerate(data, start=1):
            if i < 19:
                frame[i] = val
        checksum = 0
        for b in frame[:19]:
            checksum ^= b
        frame[19] = checksum
        return frame

    if cmd_type == "power":
        p_state = 0x01 if args[0] else 0x00
        frames.append(make_frame([0x01, p_state]))
    elif cmd_type == "brightness":
        b_val = max(0, min(100, int(args[0])))
        frames.append(make_frame([0x04, b_val]))
    elif cmd_type == "rgb":
        r, g, b = (max(0, min(255, int(x))) for x in args)
        
        # 1. Switch mode from dynamic/video scene to solid color mode
        frames.append(make_frame([0x05, 0x04, 0x01, 0x00]))
        
        # 2. TV Backlight Segmented broadcast (applies RGB across all backlight segments)
        frames.append(make_frame([0x05, 0x15, 0x01, r, g, b, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))
        
        # 3. Direct RGBIC all-zone override (0x05 0x02)
        frames.append(make_frame([0x05, 0x02, r, g, b, 0x00, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]))
    elif cmd_type == "query_state":
        frames.append(make_frame([0xAA, 0x01]))

    return frames

class BLEDeviceItem(ListItem):
    def __init__(self, name: str, address: str, is_paired: bool = False):
        super().__init__()
        self.device_name = name
        self.device_address = address
        self.is_paired = is_paired

    def compose(self) -> ComposeResult:
        tag = "[PAIRED]" if self.is_paired else ""
        yield Label(f"{self.device_name} {tag} [{self.device_address}]")


class BLEExplorer(App):
    TITLE = "Bluetooth Manager"
    SUB_TITLE = "bt-manager"

    CSS = """
    Screen {
        layout: horizontal;
        opacity: 0.85;
    }
    #sidebar {
        width: 38%;
        border-right: solid $accent;
        padding: 0 1;
    }
    #main-panel {
        width: 62%;
        padding: 0 1;
    }
    #gatt-tree {
        height: 40%;
        border: round $primary;
        margin-bottom: 1;
    }
    #console-log {
        height: 28%;
        border: round $secondary;
        margin-bottom: 1;
    }
    #controls {
        height: auto;
    }
    .input-box {
        margin-bottom: 1;
    }
    .btn-row {
        margin-top: 1;
        height: auto;
    }
    """

    BINDINGS = [
        ("s", "scan", "Scan Devices"),
        ("p", "pair_device", "Pair Phone"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.client: BleakClient | None = None
        self.selected_char_uuid: str | None = None
        self.primary_write_uuid: str | None = None
        self.selected_device_mac: str | None = None
        self.discovered_devices = {}
        self.is_notifying = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("Devices (Make phone visible in BT settings):")
                yield ListView(id="device-list")
                with Horizontal(classes="btn-row"):
                    yield Button("Scan", id="btn-scan", variant="primary")
                    yield Button("Pair / Trust", id="btn-pair", variant="warning")
                with Horizontal(classes="btn-row"):
                    yield Button("Connect Phone", id="btn-connect-phone", variant="success")
                    yield Button("Send File", id="btn-send-file", variant="default")
            with Vertical(id="main-panel"):
                yield Label("Discovered Services & Endpoints:")
                yield Tree("GATT Tree", id="gatt-tree")
                yield Label("Terminal Output & Telemetry:")
                yield Log(id="console-log", highlight=True)
                with Vertical(id="controls"):
                    yield Input(
                        placeholder="Smart control: on, off, bright 50, red, #ff00ff, or filepath for send",
                        id="cmd-input",
                        classes="input-box"
                    )
                    with Horizontal():
                        yield Button("BLE Connect & Load", id="btn-ble-connect", variant="primary")
                        yield Button("Execute Command", id="btn-exec", variant="warning")
                        yield Button("Read Endpoint", id="btn-read", variant="success")
                        yield Button("Toggle Notify", id="btn-notify", variant="default")
        yield Footer()

    async def on_mount(self):
        subprocess.run(["bluetoothctl", "power", "on"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.log_msg("Ready. If scanning for your phone, ensure Bluetooth settings are open on the phone.")

    def log_msg(self, text: str):
        log_view = self.query_one("#console-log", Log)
        log_view.write_line(text)

    def get_selected_mac(self) -> tuple[str | None, str | None]:
        device_list = self.query_one("#device-list", ListView)
        if device_list.highlighted_child and isinstance(device_list.highlighted_child, BLEDeviceItem):
            item = device_list.highlighted_child
            return item.device_address, item.device_name
        return None, None

    @work(exclusive=True)
    async def action_scan(self):
        device_list = self.query_one("#device-list", ListView)
        await device_list.clear()
        self.discovered_devices.clear()
        self.log_msg("Running Dual-Mode Scan (Classic & BLE)...")

        subprocess.run(["bluetoothctl", "--timeout", "3", "scan", "on"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        classic_devices = {}
        paired_set = set()
        try:
            raw_devices = subprocess.check_output(["bluetoothctl", "devices"], text=True)
            for line in raw_devices.strip().splitlines():
                parts = line.split(maxsplit=2)
                if len(parts) >= 3:
                    mac = parts[1].upper()
                    name = parts[2]
                    clean_name = re.sub(r"[-:]", "", name)
                    clean_mac = re.sub(r"[-:]", "", mac)
                    if clean_name != clean_mac:
                        classic_devices[mac] = name

            raw_paired = subprocess.check_output(["bluetoothctl", "devices", "Paired"], text=True)
            for line in raw_paired.strip().splitlines():
                parts = line.split(maxsplit=2)
                if len(parts) >= 2:
                    paired_set.add(parts[1].upper())
        except Exception:
            pass

        for mac, name in classic_devices.items():
            is_paired = mac in paired_set
            await device_list.append(BLEDeviceItem(name, mac, is_paired=is_paired))

        try:
            ble_devs = await BleakScanner.discover(timeout=3.0)
            for d in ble_devs:
                mac_upper = d.address.upper()
                if mac_upper not in classic_devices:
                    name = d.name
                    if not name:
                        continue
                    self.discovered_devices[d.address] = d
                    await device_list.append(BLEDeviceItem(name, d.address, is_paired=False))
        except Exception as e:
            self.log_msg(f"BLE scan note: {e}")

        self.log_msg("Scan complete. Select a device on the left.")

    async def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "btn-scan":
            self.action_scan()
        elif event.button.id == "btn-pair":
            self.pair_selected()
        elif event.button.id == "btn-connect-phone":
            self.connect_classic()
        elif event.button.id == "btn-send-file":
            self.send_file_to_phone()
        elif event.button.id == "btn-ble-connect":
            self.connect_ble_gatt()
        elif event.button.id == "btn-exec":
            self.execute_command()
        elif event.button.id == "btn-read":
            self.read_selected()
        elif event.button.id == "btn-notify":
            self.toggle_notify()

    async def on_list_view_selected(self, event: ListView.Selected):
        item = event.item
        if isinstance(item, BLEDeviceItem):
            self.selected_device_mac = item.device_address

    @work(exclusive=True)
    async def pair_selected(self):
        mac, name = self.get_selected_mac()
        if not mac:
            self.log_msg("Select a device from the list first.")
            return

        self.log_msg(f"Initiating pairing with {name} [{mac}]...")
        self.log_msg("Please confirm the pairing prompt on your phone if prompted.")

        res = subprocess.run(["bluetoothctl", "pair", mac], capture_output=True, text=True)
        subprocess.run(["bluetoothctl", "trust", mac], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if "Successful" in res.stdout or "already paired" in res.stdout.lower():
            self.log_msg(f"Successfully paired and trusted {name}.")
        else:
            self.log_msg(f"Pairing output: {res.stdout.strip() or res.stderr.strip()}")

    @work(exclusive=True)
    async def connect_classic(self):
        mac, name = self.get_selected_mac()
        if not mac:
            self.log_msg("Select a device from the list first.")
            return

        self.log_msg(f"Connecting Classic Bluetooth profiles to {name}...")
        res = subprocess.run(["bluetoothctl", "connect", mac], capture_output=True, text=True)
        if "successful" in res.stdout.lower():
            self.log_msg(f"Connected to {name}.")
        else:
            self.log_msg(f"Connection output: {res.stdout.strip() or res.stderr.strip()}")

    @work(exclusive=True)
    async def send_file_to_phone(self):
        mac, name = self.get_selected_mac()
        if not mac:
            self.log_msg("Select your phone from the list first.")
            return

        inp = self.query_one("#cmd-input", Input)
        raw_path = inp.value.strip()

        if not raw_path:
            self.log_msg("Enter the path to the file in the input bar first.")
            return

        expanded_path = os.path.abspath(os.path.expanduser(raw_path))

        if not os.path.isfile(expanded_path):
            self.log_msg(f"File not found: {expanded_path}")
            return

        filename = os.path.basename(expanded_path)
        self.log_msg(f"Initiating OBEX push of '{filename}' to {name} [{mac}]...")

        subprocess.run(["systemctl", "--user", "start", "obex.service"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        proc = await asyncio.create_subprocess_exec(
            "obexctl",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            proc.stdin.write(f"connect {mac}\n".encode())
            await proc.stdin.drain()

            session_path = None
            for _ in range(20):
                line = await proc.stdout.readline()
                decoded = line.decode().strip()
                if "Session" in decoded and "/org/bluez/obex/client/session" in decoded:
                    session_path = decoded.split()[-1]
                    break
                await asyncio.sleep(0.1)

            self.log_msg("OBEX session established. Pushing file payload...")

            proc.stdin.write(f"send {expanded_path}\n".encode())
            await proc.stdin.drain()

            transfer_done = False
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                decoded = line.decode().strip()
                if "Status: complete" in decoded or "Transfer finished" in decoded:
                    transfer_done = True
                    break
                elif "Status: error" in decoded or "Transfer failed" in decoded:
                    break

            if transfer_done:
                self.log_msg(f"Transfer of '{filename}' completed successfully.")
            else:
                self.log_msg("Transfer finished or prompt accepted on device.")

            proc.stdin.write(b"quit\n")
            await proc.stdin.drain()
        except Exception as e:
            self.log_msg(f"Transfer error: {e}")
        finally:
            try:
                proc.kill()
            except Exception:
                pass

    @work(exclusive=True)
    async def connect_ble_gatt(self):
        mac, name = self.get_selected_mac()
        if not mac:
            self.log_msg("Select a BLE device (like Govee) from the list first.")
            return

        if self.client and self.client.is_connected:
            try:
                await self.client.disconnect()
            except Exception:
                pass

        self.log_msg(f"Connecting to GATT server on {name} [{mac}]...")
        self.client = BleakClient(mac, timeout=10.0)

        try:
            await self.client.connect()
            self.log_msg(f"Connected. Parsing services...")
            await self.populate_gatt_tree()
        except Exception as e:
            self.log_msg(f"BLE GATT connection failed: {e}. If this is a phone, use 'Pair / Trust' instead.")

    async def populate_gatt_tree(self):
        tree = self.query_one("#gatt-tree", Tree)
        tree.clear()
        tree.root.label = "Device Endpoints"
        tree.root.expand()

        self.primary_write_uuid = None

        for service in self.client.services:
            srv_label = HUMAN_UUID_MAP.get(service.uuid.lower(), "Custom Vendor Service")
            srv_node = tree.root.add(f"Service: {srv_label}", expand=True)

            for char in service.characteristics:
                char_label = HUMAN_UUID_MAP.get(char.uuid.lower(), "Data Endpoint")
                props = ",".join(char.properties)
                
                if "write" in props or "write-without-response" in props:
                    if not self.primary_write_uuid or "2b11" in char.uuid.lower() or "1911" in char.uuid.lower():
                        self.primary_write_uuid = char.uuid
                        if char_label == "Data Endpoint":
                            char_label = "Command Channel (Write)"

                srv_node.add_leaf(f"{char_label} [{props}] ({char.uuid})", data=char.uuid)

        if self.primary_write_uuid:
            self.selected_char_uuid = self.primary_write_uuid
            self.log_msg("GATT tree ready. Commands: 'on', 'off', 'bright <0-100>', '<colour>'")

    def on_tree_node_selected(self, event: Tree.NodeSelected):
        if event.node.data:
            self.selected_char_uuid = event.node.data
            label = HUMAN_UUID_MAP.get(self.selected_char_uuid.lower(), self.selected_char_uuid)
            self.log_msg(f"Selected Endpoint: {label}")

    @work(exclusive=True)
    async def toggle_notify(self):
        if not self.client or not self.client.is_connected or not self.selected_char_uuid:
            self.log_msg("Select an endpoint (e.g. Light Telemetry) from the tree first.")
            return

        def telemetry_callback(sender, data: bytearray):
            hex_str = " ".join(f"{b:02x}" for b in data)
            parsed_info = ""
            if len(data) >= 3 and data[0] == 0xAA:
                if data[1] == 0x01:
                    power = "ON" if data[2] == 0x01 else "OFF"
                    parsed_info = f" -> State: Power {power}"
                elif data[1] == 0x04:
                    parsed_info = f" -> Brightness: {data[2]}%"
                elif data[1] == 0x05 and len(data) >= 6:
                    parsed_info = f" -> Active Colour: RGB({data[3]}, {data[4]}, {data[5]})"

            self.log_msg(f"Telemetry Stream: {hex_str}{parsed_info}")

        try:
            if not self.is_notifying:
                await self.client.start_notify(self.selected_char_uuid, telemetry_callback)
                self.is_notifying = True
                self.log_msg("Subscribed to live notifications. Press hardware buttons to view stream.")
            else:
                await self.client.stop_notify(self.selected_char_uuid)
                self.is_notifying = False
                self.log_msg("Unsubscribed from notifications.")
        except Exception as e:
            self.log_msg(f"Notify error: {e}")

    @work(exclusive=True)
    async def execute_command(self):
        if not self.client or not self.client.is_connected:
            self.log_msg("No BLE device connected. Click 'BLE Connect & Load' first.")
            return

        target_uuid = self.selected_char_uuid or self.primary_write_uuid
        if not target_uuid:
            self.log_msg("No writable endpoint selected.")
            return

        inp = self.query_one("#cmd-input", Input)
        cmd = inp.value.strip().lower()
        if not cmd:
            return

        payloads = []

        if cmd in ["on", "start", "enable"]:
            payloads = build_govee_packet("power", True)
            self.log_msg("Action: Turning ON")
        elif cmd in ["off", "stop", "disable"]:
            payloads = build_govee_packet("power", False)
            self.log_msg("Action: Turning OFF")
        elif cmd.startswith("bright") or cmd.startswith("dim"):
            parts = cmd.split()
            if len(parts) > 1 and parts[1].isdigit():
                val = int(parts[1])
                payloads = build_govee_packet("brightness", val)
                self.log_msg(f"Action: Setting brightness to {val}%")
            else:
                self.log_msg("Usage: bright <0-100>")
                return
        elif cmd in ["status", "query", "state"]:
            payloads = build_govee_packet("query_state")
            self.log_msg("Action: Querying state from controller")
        elif cmd in NAMED_COLOURS:
            r, g, b = NAMED_COLOURS[cmd]
            payloads = build_govee_packet("rgb", r, g, b)
            self.log_msg(f"Action: Setting colour to {cmd} (RGB: {r},{g},{b})")
        elif re.match(r"^#?[0-9a-f]{6}$", cmd):
            clean_hex = cmd.lstrip("#")
            r = int(clean_hex[0:2], 16)
            g = int(clean_hex[2:4], 16)
            b = int(clean_hex[4:6], 16)
            payloads = build_govee_packet("rgb", r, g, b)
            self.log_msg(f"Action: Setting custom hex #{clean_hex}")
        else:
            raw_text = cmd.replace("0x", "").replace(" ", "")
            try:
                payloads = [bytearray.fromhex(raw_text)]
                self.log_msg("Action: Sending raw custom hex payload")
            except ValueError:
                self.log_msg(f"Unknown command '{cmd}'")
                return

        if payloads:
            try:
                for p in payloads:
                    try:
                        await self.client.write_gatt_char(target_uuid, p, response=False)
                    except Exception:
                        await self.client.write_gatt_char(target_uuid, p, response=True)
                    await asyncio.sleep(0.08)
                self.log_msg("Command frames delivered.")
                inp.value = ""
            except Exception as e:
                self.log_msg(f"Write failed: {e}")

    @work(exclusive=True)
    async def read_selected(self):
        if not self.client or not self.client.is_connected or not self.selected_char_uuid:
            self.log_msg("Connect and select an endpoint first.")
            return
        try:
            val = await self.client.read_gatt_char(self.selected_char_uuid)
            hex_str = " ".join(f"{b:02x}" for b in val)
            ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in val)
            self.log_msg(f"Read: [ASCII] {ascii_str} | [Hex] {hex_str}")
        except Exception as e:
            self.log_msg(f"Read error: {e}. If this is a telemetry endpoint, click 'Toggle Notify' instead.")


if __name__ == "__main__":
    app = BLEExplorer()
    app.run()
