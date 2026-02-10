"""
enteliscript.py

CLI for enteliweb.
"""
from enteliweb import EnteliWEB



if __name__ == "__main__":
    api = EnteliWEB(username="admin", password="password", server_ip="192.168.1.100", site_name="DefaultSite")
