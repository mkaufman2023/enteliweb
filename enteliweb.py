"""
`enteliweb.py`

Wrapper for the `enteliWEB` REST API.

Hierarchy:
    1. Site (Building)
    2. Device (Controller 100)
    3. Object (Analog Input 1)
    4. Property (Present_Value: 72.5)

See:
    - https://gemini.google.com/share/e632d5107114
    - https://chatgpt.com/share/6988f56c-e5b8-800e-a1ac-03bf4d9f7b14
    - https://claude.ai/share/aef2a9ab-812c-47aa-afa5-47f89405f9f9
"""
import os
import time
import json
import socket
import requests
from rich import box
from rich.table import Table
from rich.panel import Panel
from rich.theme import Theme
from rich.console import Console



class EnteliWEB:
    """
    Class for interacting with the `enteliWEB` API.

    ## Init Parameters
    - `username`: The username for the enteliWEB API.
    - `password`: The password for the enteliWEB API.
    - `server_ip`: The IP address of the enteliWEB server. If not provided, the local machine's IP will be used.
    """
    console = Console(theme=Theme({
        "info": "cyan",
        "warn": "yellow",
        "ok": "bold green",
        "error": "bold red",
        "misc": "bold blue",
        "debug": "dim white",
        "trace": "bold magenta",
    }))

    def __init__(self, username: str, password: str, server_ip: str = None) -> None:
        """
        """
        self.username = username
        self.password = password
        self.server = (
            socket.gethostbyname(socket.gethostname()) 
            if (server_ip is None) else server_ip.split("://")[-1]
        )
        self.session_id = ""
        self.csrf_token = ""
        self.session_key = "enteliWebID"
        self.csrf_token_key = "_csrfToken"
        self.base_url = "/enteliweb/api/.bacnet/"

        self.console.log("Initialized EnteliWEB instance.")
        # self.console.print(Panel(f"Username:  {username}\nPassword:  {password}\nServer IP: {server_ip}\nSite name: {site_name}", border_style="cyan"))
        # info_table = Table(title="EnteliWEB Info", show_header=True, box=box.ROUNDED)
        # info_table.add_column("Field", style="cyan", no_wrap=True)
        # info_table.add_column("Value", style="magenta")
        # info_table.add_row("Username", username)
        # info_table.add_row("Password", password)
        # info_table.add_row("Server", server_ip)
        # info_table.add_row("Sitename", site_name)
        # self.console.print(info_table)



    def login(self) -> bool:
        """
        *Endpoint:* `/api/auth/basiclogin`

        Retrieves the session ID and CSRF token and stores them for future requests.

        ## Returns
        - `True` if login was successful, `False` otherwise.
        """
        self.console.log(f"Attempting to log in to {self.server} as {self.username}[white]...[/white]")

        try:
            r = requests.get(
                url = f"http://{self.server}/enteliweb/api/auth/basiclogin?alt=JSON",
                auth = (self.username, self.password),
                headers = {'Content-Type': 'application/json'}
            )
        except Exception as e:
            self.console.log(f"  Error during login request: {e}")
            return False

        if (r.status_code != requests.codes.ok):
            self.console.log(f"  Login request failed ({r.status_code}): {r.reason}")
            return False
        
        if (r.text.find('Cannot Connect') > -1):
            self.console.log(f"  Login failed: {r.text}")
            return False
        
        if (not self.session_key in r.cookies.keys()):
            self.console.log(f"  Login failed: {r.text}")
            return False
        
        result = r.json()
        self.session_id = r.cookies[self.session_key]
        self.csrf_token = result[self.csrf_token_key]

        self.console.log("  Login was successful.")
        return True
    


    def create_object(self, site_name: str, device: str, object_type: str, instance: str, name: str, properties: dict = {}) -> bool:
        """
        *Endpoint:* `/api/.bacnet/{site}/{device}`

        Creates a new BACnet object for a device.

        ## Parameters
        - `site_name`: The site that contains the target device. 
        - `device`: The device address in which to create the object.
        - `object_type`: The name of BACnet object to create (e.g., `AI`, `AO`, `AV`, etc.).
        - `instance`: The instance number of the BACnet object.
        - `name`: The desired name of the BACnet object.
        - *(Optional)* `properties`:  A dictionary of additional properties to set on the BACnet object.

        ## Returns
        - `True` if the object was created successfully, `False` otherwise.
        """
        if (self.session_id == ""):
            self.console.log("Unable to create object: Not logged in.")
            return False
        
        self.console.log(f"Attempting to create object with name [yellow]{name}[/yellow] and ID [yellow]{object_type},{instance}[/yellow][white]...[/white]")

        data = {
            "$base": "Object",
            "object-identifier": {
                "$base": "ObjectIdentifier",
                "value": f"{object_type},{instance}"
            },
            "object-name": {
                "$base": "String",
                "value": name
            },
        }

        for property in properties:
            data[property] = { "$base": "String", "value": properties[property] }

        r = requests.post(
            url = f"http://{self.server}{self.base_url}{site_name}/{device}?alt=JSON&{self.csrf_token_key}={self.csrf_token}",
            cookies = {self.session_key: self.session_id},
            headers = {'Content-Type': 'application/json'},
            data = json.dumps(data),
        )

        success, code, msg = self._check_error(r)
        if (not success or msg != "Created"):
            self.console.log(f"  Failed to create object.")
            self.console.log(f"  Response code: {code}")
            self.console.log(f"  Response message: {msg}")
            return False
        self.console.log(f"  Successfully created object.")
        return r.reason == requests.codes.created
    


    def delete_object(self, site_name: str, device: str, object_type: str, instance: str) -> bool:
        """
        *Endpoint:* `/api/.bacnet/{site}/{device}/{object_type},{instance}`

        Deletes a BACnet object from a device.

        ## Parameters
        - `site_name`: The site that contains the target device.
        - `device`: The device address from which to delete the object.
        - `object_type`: The name of the BACnet object to delete (e.g., `AI`, `AO`, `AV`, etc.).
        - `instance`: The instance number of the BACnet object.

        ## Returns
        - `True` if the object was deleted successfully, `False` otherwise.
        """
        if (self.session_id == ""):
            self.console.log("Unable to delete object: Not logged in.")
            return False

        self.console.log(f"Attempting to delete object with ID [yellow]{object_type},{instance}[/yellow][white]...[/white]")

        r = requests.delete(
            url = f"http://{self.server}{self.base_url}{site_name}/{device}/{object_type},{instance}?alt=JSON&{self.csrf_token_key}={self.csrf_token}",
            cookies = {self.session_key: self.session_id},
        )

        success, code, msg = self._check_error(r)
        if (r.status_code != requests.codes.non_authoritative_info):
            self.console.log(f"  Failed to delete object.")
            self.console.log(f"  Response code: {code}")
            self.console.log(f"  Response message: {msg}")
            return False
        self.console.log(f"  Successfully deleted object.")
        return True

    

    def write_property(self, site_name: str, device: str, object_type: str, instance: str, property_name: str, value: str) -> bool:
        """
        *Endpoint:* `/api/.bacnet/<site>/<device>/<object_type>,<instance>/<property_name>`

        Writes a value to a BACnet object's property.

        ## Parameters
        - `site_name`: The site that contains the target device.
        - `device`: The device address that contains the target object.
        - `object_type`: The type of the BACnet object (e.g., `AI`, `AO`, `AV`, etc.).
        - `instance`: The instance number of the BACnet object.
        - `property_name`: The name of the property to write.
        - `value`: The value to write to the property.

        ## Returns
        - `True` if the property was written successfully, `False` otherwise.
        """
        if (self.session_id == ""):
            self.console.log("Unable to write property: Not logged in.")
            return False
        
        self.console.log(f"Attempting to write property [yellow]{property_name}[/yellow] with value [yellow]{value}[/yellow][white]...[/white]")
        
        # Detect sub-property and array index
        property_name = property_name.replace('[', '.').replace(']', '').replace('.', '/')

        r = requests.put(
            url = f"http://{self.server}{self.base_url}{site_name}/{device}/{object_type},{instance}/{property_name}?alt=JSON&{self.csrf_token_key}={self.csrf_token}",
            cookies = {self.session_key: self.session_id},
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
                "$base": "String",
                "value": value,
            }),
        )

        success, code, msg = self._check_error(r)
        if (r.status_code != requests.codes.ok):
            self.console.log(f"  Failed to write property.")
            self.console.log(f"  Response code: {code}")
            self.console.log(f"  Response message: {msg}")
            return False
        self.console.log(f"  Successfully wrote property.")
        return True
    


    def write_properties(self, site_name: str, device: str, object_type: str, instance: str, properties: dict) -> bool:
        """
        *Endpoint:* `/api/.multi`

        Writes multiple properties to a BACnet object.

        ## Parameters
        - `site_name`: The site that contains the target device.
        - `device`: The device address that contains the target object.
        - `object_type`: The type of the BACnet object (e.g., `AI`, `AO`, `AV`, etc.).
        - `instance`: The instance number of the BACnet object.
        - `properties`: A dictionary of property names and values to write.

        ## Returns
        - `True` if all properties were written successfully, `False` otherwise.
        """
        if (self.session_id == ""):
            self.console.log("Unable to write properties: Not logged in.")
            return False
        
        self.console.log(f"Attempting to write multiple properties to [yellow]{object_type},{instance}[/yellow] on device [yellow]{device}[/yellow][white]...[/white]")

        value_list = {
            "$base": "List",
        }

        for i, property in enumerate(properties, start=1):
            value_list[i] = {
                "$base": "String",
                "via": f"/.bacnet/{site_name}/{device}/{object_type},{instance}/{property}",
                "value": properties[property]
            }

        r = requests.post(
            url = f"http://{self.server}/enteliweb/api/.multi?alt=json&{self.csrf_token_key}={self.csrf_token}",
            cookies = {self.session_key: self.session_id},
            headers = {'Content-Type': 'application/json'},
            data = json.dumps({
                "$base": "Struct",
                "values": value_list,
            }),
        )

        success, code, msg = self._check_error(r)
        if (r.reason != requests.codes.ok):     # TODO: CHECK THIS LOGIC
            self.console.log(f"  Failed to write properties.")
            self.console.log(f"  Response code: {code}")
            self.console.log(f"  Response message: {msg}")
            return False
        self.console.log(f"  Successfully wrote properties.")
        return True



    def get_sites(self) -> list[str]:
        """
        *Endpoint:* `/api/.bacnet`

        Gets all sites for the current enteliWEB server.

        ## Returns
        - A list of sites, or an empty list if none are found.
        """
        if (self.session_id == ""):
            self.console.log("Unable to get sites: Not logged in.")
            return False
        
        self.console.log("Attempting to get sites[white]...[/white]")

        r = requests.get(
            url = f"http://{self.server}{self.base_url}?alt=JSON&{self.csrf_token_key}={self.csrf_token}",
            cookies = {self.session_key: self.session_id},
            headers = {'Content-Type': 'application/json'},
        )

        success, code, msg = self._check_error(r)
        if (success is not True):
            self.console.log(f"  Failed to get sites.")
            self.console.log(f"  Response code: {code}")
            self.console.log(f"  Response message: {msg}")
            return []
        
        result = r.json()
        self.console.log(f"  Successfully got sites.")
        return [
            key
            for key in sorted(result)
            if ("nodeType" in result[key] and result[key]["nodeType"] == "NETWORK")
        ]



    def get_devices(self, site_name: str) -> list[str]:
        """
        *Endpoint:* `/api/.bacnet/<site_name>`

        Gets all devices for a given site.

        ## Parameters
        - `site_name`: The name of the site to get devices for.

        ## Returns
        - A list of devices, or an empty list if none are found.
        """
        def custom_key(x):
            try: return int(x)
            except: return 0

        if (self.session_id == ""):
            self.console.log("Unable to get devices: Not logged in.")
            return False
        
        self.console.log(f"Attempting to get devices for site [yellow]{site_name}[/yellow][white]...[/white]")

        r = requests.get(
            url = f"http://{self.server}{self.base_url}{site_name}?alt=JSON&{self.csrf_token_key}={self.csrf_token}",
            cookies = {self.session_key: self.session_id},
            headers = {'Content-Type': 'application/json'},
        )

        if (r.status_code != requests.codes.ok):
            self.console.log(f"  Failed to get devices.")
            self.console.log(f"  Response code: {r.status_code}")
            self.console.log(f"  Response message: {r.reason}")
            return []
        
        result = r.json()
        self.console.log(f"  Successfully got sites.")
        return [
            f"{key} - {result[key]['displayName']}"
            for key in sorted(result, key=custom_key)
            if ("nodeType" in result[key] and result[key]["nodeType"] == "DEVICE")
        ]



    def get_objects(self, site_name: str, device: str) -> list[str]:
        """
        *Endpoint:* `/api/.bacnet/<site_name>/<device>`

        Gets all BACnet objects for a given device on a specific site.

        ## Parameters
        - `site_name`: The name of the site that contains the target device.
        - `device`: The device address to get objects for.

        ## Returns
        - A list of BACnet objects, or an empty list if none are found.
        """
        if (self.session_id == ""):
            self.console.log("Unable to get objects: Not logged in.")
            return False
        
        self.console.log(f"Attempting to get objects for device [yellow]{device}[/yellow] on site [yellow]{site_name}[/yellow][white]...[/white]")
        
        objects = []

        # TODO: check '/' following <device> in url for issue
        r = requests.get(
            url = f"http://{self.server}{self.base_url}{site_name}/{device}/?alt=JSON&{self.csrf_token_key}={self.csrf_token}",
            cookies = {self.session_key: self.session_id},
            headers = {'Content-Type': 'application/json'},
        )

        if (r.status_code != requests.codes.ok):
            self.console.log(f"  Failed to get objects.")
            self.console.log(f"  Response code: {r.status_code}")
            self.console.log(f"  Response message: {r.reason}")
            return []
        
        result = r.json()
        self.console.log(f"  Successfully got objects.")
        return [
            key
            for key in sorted(result)
            if ("$base" in result[key] and result[key]["$base"] == "Object")
        ]



    def _check_error(self, response: requests.Response) -> tuple[bool, int, str]:
        """
        Checks a response for errors.

        ## Parameters
        - `response`: The response object to check.

        ## Returns
        - `success`: `True` if the request was successful, `False` otherwise.
        - `code`: The HTTP status code of the response.
        - `msg`: The error message, if any.
        """
        result = response.json() if (response.status_code == requests.codes.ok) else {}

        if ("error" in result and result["error"] != "-1"):
            code = result["error"]
            msg	= result["errorText"]
        else:
            if (response.status_code == requests.codes.non_authoritative_info):
                code = str(requests.codes.ok)
                msg = "OK"
            else:
                code = str(response.status_code)
                msg	= response.reason

        success = (code == str(response.status_code))
        return (success, code, msg)
    


    def _find_abbreviation(self, bacnet_object_name: str) -> str:
        """
        Resolves a BACnet object name (e.g., `analog-input`, `trend-log`, etc.) to its corresponding abbreviation.

        ## Parameters
        - `bacnet_object_name`: The name of the BACnet object to resolve.

        ## Returns
        - The abbreviation of the BACnet object name if found, else an empty string.
        """
        object_name_map = {
            "ACC": "access-credential",         "EL": "event-log",
            "ACD": "access-door",               "FIL": "file",
            "ACP": "access-point",              "GGP": "global-group",
            "ACR": "access-rights",             "GR": "group",
            "ACU": "access-user",               "IV": "integer-value",
            "ACZ": "access-zone",               "LAV": "large-analog-value",
            "AC": "accumulator",                "ZP": "life-safety-point",
            "AIC": "aic",                       "ZN": "life-safety-zone",
            "AE": "alert-enrollment",           "LO": "lighting-output",
            "AI": "analog-input",               "LS": "load-control",
            "AO": "analog-output",              "CO": "loop",
            "AV": "analog-value",               "MIC": "mic",
            "AOC": "aoc",                       "MOC": "moc",
            "AT": "at",                         "MT": "mt",
            "AVG": "averaging",                 "MI": "multi-state-input",
            "BDC": "bdc",                       "MO": "multi-state-output",
            "BDE": "bde",                       "MV": "multi-state-value",
            "BI": "binary-input",               "NET": "net",
            "BO": "binary-output",              "NS": "network-security",
            "BV": "binary-value",               "EVC": "notification-class",
            "BSV": "bitstring-value",           "NF": "notification-forwarder",
            "BT": "bt",                         "OSV": "octetstring-value",
            "CAL": "calendar",                  "ORS": "ors",
            "CNL": "channel",                   "OS": "os",
            "CSV": "characterstring-value",     "PI": "pi",
            "CS": "command",                    "PIV": "positive-integer-value",
            "ACI": "credential-data-input",     "PG": "program",
            "DPValue": "date-pattern-value",    "PC": "pulse-converter",
            "DV": "date-value",                 "SCH": "schedule",
            "DTP": "datetime-pattern-value",    "SV": "structured-view",
            "DTV": "datetime-value",            "TPV": "time-pattern-value",
            "DES": "des",                       "TV": "time-value",
            "DEV": "device",                    "TL": "trend-log",
            "DRT": "drt",                       "TLM": "trend-log-multiple",
            "EV": "event-enrollment",           "Unassigned 1": "unassigned-1",
        }
        for object_abbreviation, mapped_bacnet_object_name in object_name_map.items():
            if bacnet_object_name == mapped_bacnet_object_name:
                return object_abbreviation
        return ""





if __name__ == "__main__":
    api = EnteliWEB(username="admin", password="password", server_ip="192.168.1.100", site_name="DefaultSite")
