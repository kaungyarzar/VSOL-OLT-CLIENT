import re
from vsol_olt_client.connection import Connection
from enum import Enum

class CLI_MODE(Enum):
    PRI = '> '
    ALT = '# '
    CONF = '(config)# '

def enable_pri_mode(conn: Connection):
    p = conn.get_shell_prompt()
    if not p.endswith(CLI_MODE.PRI.value):
        # `exit` command doesn't work.
        conn.logout()
    conn.login()

def enable_alt_mode(conn: Connection):
    p = conn.get_shell_prompt()
    if p.endswith(CLI_MODE.CONF.value):
        conn.send('exit')
        conn.expect([CLI_MODE.ALT.value])
    if p.endswith(CLI_MODE.PRI.value):
        conn.send('enable')
        conn.expect(['Password: '])
        conn.send(conn.password)
        conn.expect([CLI_MODE.ALT.value])

def enable_conf_mode(conn: Connection):
    p = conn.get_shell_prompt()
    if CLI_MODE.CONF.value in p:
        return

    if p.endswith(CLI_MODE.PRI.value):
        conn.send('enable')
        conn.expect(['Password: '])
        conn.send(conn.password)
        conn.expect([CLI_MODE.ALT.value])

    conn.send('configure terminal')
    conn.expect([CLI_MODE.CONF.value])

def get_hostname(conn: Connection) -> str:
    p = conn.get_shell_prompt()
    return re.sub('> |\(config\)# |# ','', p)

def get_running_config(conn: Connection) -> str:
    enable_alt_mode(conn)
    p = conn.get_shell_prompt()
    cmd = 'show running-config'
    conn.send(cmd)
    _, res = conn.expect([p])
    config = res.strip(cmd).strip(p)
    return config

def get_version(conn: Connection) -> dict:
    enable_conf_mode(conn)
    p = conn.get_shell_prompt()
    cmd = 'show version'
    conn.send(cmd)
    _, res = conn.expect([p])
    patterns = {
        "serial_number": r"Olt Serial Number:\s+(\S+)",
        "device_model": r"Olt Device Model:\s+(\S+)",
        "hardware_version": r"Hardware Version:\s+(\S+)",
        "software_version": r"Software Version:\s+(\S+)",
        "software_created_time": r"Software Created Time:\s+(.*)"
    }
    # Parse the information using regex
    parsed_results = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, res)
        if match:
            parsed_results[key] = match.group(1)
    
    return parsed_results
