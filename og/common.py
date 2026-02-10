"""
Common data and helpers.
Used by the enteliWEB API, and enteliSCRIPT.

Copyright (C) Delta Controls Inc. 2016
"""

OBJECT_NAME_MAP = {
    "AI": "analog-input",
    "AO": "analog-output",
    "AV": "analog-value",
    "BI": "binary-input",
    "BO": "binary-output",
    "BV": "binary-value",
    "CAL": "calendar",
    "CS": "command",
    "DEV": "device",
    "EV": "event-enrollment",
    "FIL": "file",
    "GR": "group",
    "CO": "loop",
    "MI": "multi-state-input",
    "MO": "multi-state-output",
    "EVC": "notification-class",
    "PG": "program",
    "SCH": "schedule",
    "AVG": "averaging",
    "MV": "multi-state-value",
    "TL": "trend-log",
    "ZP": "life-safety-point",
    "ZN": "life-safety-zone",
    "AC": "accumulator",
    "PC": "pulse-converter",
    "EL": "event-log",
    "GGP": "global-group",
    "TLM": "trend-log-multiple",
    "LS": "load-control",
    "SV": "structured-view",
    "ACD": "access-door",
    "Unassigned 1": "unassigned-1",
    "ACC": "access-credential",
    "ACP": "access-point",
    "ACR": "access-rights",
    "ACU": "access-user",
    "ACZ": "access-zone",
    "ACI": "credential-data-input",
    "NS": "network-security",
    "BSV": "bitstring-value",
    "CSV": "characterstring-value",
    "DPValue": "date-pattern-value",
    "DV": "date-value",
    "DTP": "datetime-pattern-value",
    "DTV": "datetime-value",
    "IV": "integer-value",
    "LAV": "large-analog-value",
    "OSV": "octetstring-value",
    "PIV": "positive-integer-value",
    "TPV": "time-pattern-value",
    "TV": "time-value",
    "NF": "notification-forwarder",
    "AE": "alert-enrollment",
    "CNL": "channel",
    "LO": "lighting-output",
    "MIC": "mic",
    "MOC": "moc",
    "AIC": "aic",
    "AOC": "aoc",
    "BDC": "bdc",
    "BT": "bt",
	"AT": "at",
	"DRT": "drt",
	"ORS": "ors",
    "BDE": "bde",
	"OS": "os",
	"MT": "mt",
	"NET": "net",
	"PI": "pi",
    "DES": "des"
}


def custom_key(x):
    """
    Support function for sorted key
    """
    try:
        return int(x)
    except:
        return 0
