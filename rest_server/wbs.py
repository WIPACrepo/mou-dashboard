"""The Work-Breakdown Structures."""


from typing import Dict, List, TypedDict

_MO = "mo"
_UPGRADE = "upgrade"
WBS_L1_VALUES = [_MO, _UPGRADE]


class _WBSTypedDict(TypedDict, total=True):
    """TypedDict for WBS."""

    L2_values: List[str]
    L3_values_by_L2: Dict[str, List[str]]


WBS: Dict[str, _WBSTypedDict] = {
    _MO: {
        "L2_values": [
            "2.1 Program Coordination",
            "2.2 Detector Operations & Maintenance (Online)",
            "2.3 Computing & Data Management Services",
            "2.4 Data Processing & Simulation Services",
            "2.5 Software",
            "2.6 Calibration",
        ],
        "L3_values_by_L2": {
            "2.1 Program Coordination": [
                "2.1.0 Program Coordination",
                "2.1.1 Administration",
                "2.1.2 Engineering and R&D Support",
                "2.1.3 USAP Support & Safety",
                "2.1.4 Education & Outreach",
                "2.1.5 Communications",
            ],
            "2.2 Detector Operations & Maintenance (Online)": [
                "2.2.0 Detector Operations & Maintenance",
                "2.2.1 Run Coordination",
                "2.2.2 Data Acquisition",
                "2.2.3 Online Filter (PnF)",
                "2.2.4 Detector Monitoring",
                "2.2.5 Experiment Control",
                "2.2.6 Surface Detectors",
                "2.2.7 Supernova System",
                "2.2.8 Real-Time Alerts",
                "2.2.9 SPS/SPTS",
            ],
            "2.3 Computing & Data Management Services": [
                "2.3.0 Computing & Data Management Services",
                "2.3.1 Data Storage & Transfer",
                "2.3.2 Core Data Center Infrastructure",
                "2.3.3 Central Computing Resources",
                "2.3.4 Distributed Computing Resources",
            ],
            "2.4 Data Processing & Simulation Services": [
                "2.4.0 Data Processing & Simulation Services",
                "2.4.1 Offline Data Production",
                "2.4.2 Simulation Production",
                "2.4.3 Public Data Products",
            ],
            "2.5 Software": [
                "2.5.0 Software",
                "2.5.1 Core Software",
                "2.5.2 Simulation Software",
                "2.5.3 Reconstruction",
                "2.5.4 Science Support Tools",
                "2.5.5 Software Development Infrastructure",
            ],
            "2.6 Calibration": [
                "2.6.0 Calibration",
                "2.6.1 Detector Calibration",
                "2.6.2 Ice Properties",
            ],
        },
    },
    _UPGRADE: {"L2_values": [], "L3_values_by_L2": {}},
}