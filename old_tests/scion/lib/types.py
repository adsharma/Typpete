class TypeBase(object):
    pass


############################
# Basic types
############################
class AddrType(TypeBase):
    NONE = 0
    IPV4 = 1
    IPV6 = 2
    SVC = 3
    UNIX = 4  # For dispatcher socket


class ExtensionClass(TypeBase):
    """
    Constants for two types of extensions. These values are shared with L4
    protocol values, and an appropriate value is placed in next_hdr type.
    """

    HOP_BY_HOP = 0
    END_TO_END = 222  # (Expected:-) number for SCION end2end extensions.


class ExtHopByHopType(TypeBase):
    TRACEROUTE = 0
    SIBRA = 1
    SCMP = 2
    ONE_HOP_PATH = 3


class ExtEndToEndType(TypeBase):
    PATH_TRANSPORT = 0
    PATH_PROBE = 1


class L4Proto(TypeBase):
    NONE = 0
    SCMP = 1
    TCP = 6
    UDP = 17
    SSP = 152
    L4 = SCMP, TCP, UDP, SSP


############################
# Payload class/types
############################
class PayloadClass(object):
    PCB = "pcb"
    IFID = "ifid"
    CERT = "certMgmt"
    PATH = "pathMgmt"
    SIBRA = "sibra"


class CertMgmtType(object):
    CERT_CHAIN_REQ = "certChainReq"
    CERT_CHAIN_REPLY = "certChainRep"
    TRC_REQ = "trcReq"
    TRC_REPLY = "trcRep"


class PathMgmtType(object):
    REQUEST = "segReq"
    REPLY = "segReply"
    # Path registration (sent by Beacon Server).
    REG = "segReg"
    # For records synchronization purposes (used by Path Servers).
    SYNC = "segSync"
    REVOCATION = "revInfo"
    IFSTATE_REQ = "ifStateReq"
    IFSTATE_INFOS = "ifStateInfos"


class PathSegmentType(TypeBase):
    """
    PathSegmentType class, indicates a type of path request/reply.
    """

    UP = 0  # Request/Reply for up-paths
    DOWN = 1  # Request/Reply for down-paths
    CORE = 2  # Request/Reply for core-paths
    GENERIC = 3  # FIXME(PSz): experimental for now.


############################
# Router types
############################
class RouterFlag(TypeBase):
    ERROR = 0
    NO_PROCESS = 1
    # Process this locally
    PROCESS_LOCAL = 2
    # Forward packet to supplied IFID
    FORWARD = 3
    # Packet has reached its destination ISD-AS
    DELIVER = 4
    # Deliver packet even if it hasn't reached its destination ISD-AS
    FORCE_DELIVER = 5


############################
# SIBRA types
############################
class SIBRAPathType(TypeBase):
    STEADY = 0
    EPHEMERAL = 1


class LinkType(TypeBase):
    #: Link to child AS
    CHILD = "CHILD"
    #: Link to parent AS
    PARENT = "PARENT"
    #: Link to peer AS
    PEER = "PEER"
    #: Link to other core AS
    ROUTING = "ROUTING"
