"""
Protocol and service identification utilities.
Maps transport layer ports and protocol codes to standard network services.
"""

from typing import Optional, Dict

# Standard IP Protocol Numbers (RFC 790 / IANA)
IP_PROTOCOLS: Dict[int, str] = {
    1: "ICMP",
    2: "IGMP",
    6: "TCP",
    17: "UDP",
    41: "IPv6-Route",
    47: "GRE",
    50: "ESP",
    51: "AH",
    58: "ICMPv6",
    89: "OSPF",
}

# Standard Well-Known Port to Service Mapping (IANA Registered)
PORT_SERVICES: Dict[int, str] = {
    20: "FTP-Data",
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    67: "DHCP",
    68: "DHCP",
    69: "TFTP",
    80: "HTTP",
    110: "POP3",
    123: "NTP",
    143: "IMAP",
    161: "SNMP",
    162: "SNMP-Trap",
    179: "BGP",
    194: "IRC",
    443: "HTTPS",
    445: "SMB",
    465: "SMTPS",
    514: "Syslog",
    587: "SMTP-Submission",
    636: "LDAPS",
    993: "IMAPS",
    995: "POP3S",
    1433: "MSSQL",
    1521: "Oracle-DB",
    1900: "SSDP",
    3000: "Next.js-Dev",
    3306: "MySQL",
    3389: "RDP",
    5353: "mDNS",
    5432: "PostgreSQL",
    5900: "VNC",
    6379: "Redis",
    8000: "FastAPI-Dev",
    8080: "HTTP-Alt",
    8443: "HTTPS-Alt",
    9090: "Prometheus",
    27017: "MongoDB",
}


def get_protocol_name(proto_id: int) -> str:
    """Return protocol name from IP protocol number."""
    return IP_PROTOCOLS.get(proto_id, f"PROTO-{proto_id}")


def identify_service(src_port: Optional[int], dst_port: Optional[int], protocol: str = "TCP") -> str:
    """
    Identify network service using source/destination port and protocol.
    Respects networking reality: Encrypted TLS/HTTPS payloads are classified
    as HTTPS / Web Traffic without claiming unverified deep application identity.
    """
    proto_upper = protocol.upper()

    # ICMP has no ports
    if proto_upper in ("ICMP", "ICMPV6"):
        return "ICMP Ping/Control"

    # Prioritize destination port (server port), then source port
    ports_to_check = []
    if dst_port is not None:
        ports_to_check.append(dst_port)
    if src_port is not None:
        ports_to_check.append(src_port)

    for port in ports_to_check:
        if port in PORT_SERVICES:
            return PORT_SERVICES[port]

    # Common ranges
    for port in ports_to_check:
        if 49152 <= port <= 65535:
            continue  # Ephemeral client port range
        if port in (8000, 8080, 8888, 5000, 3000):
            return "Web Traffic"

    # Fallback to general protocol classification
    if proto_upper == "TCP":
        return "TCP Traffic"
    if proto_upper == "UDP":
        return "UDP Traffic"
    return "Unknown"
