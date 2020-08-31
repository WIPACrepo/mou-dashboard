"""Stub of keycloak-rest-services.

https://github.com/WIPACrepo/keycloak-rest-services/blob/master/resources/icecube_setup.py
"""


from typing import Dict, TypedDict

_US_CAN = "US and Canada"
_EUROPE = "Europe"
_ASIA_PAC = "Asia Pacific"


class InstitutionMeta(TypedDict):
    """Metadata schema for an institution."""

    cite: str
    abbreviation: str
    is_US: bool
    region: str


ICECUBE_INSTS = {
    "Aachen": {
        "cite": "III. Physikalisches Institut, RWTH Aachen University, D-52056 Aachen, Germany",
        "abbreviation": "RWTH",
        "is_US": False,
        "region": _EUROPE,
    },
    "Adelaide": {
        "cite": "Department of Physics, University of Adelaide, Adelaide, 5005, Australia",
        "abbreviation": "ADELAIDE",
        "is_US": False,
        "region": _ASIA_PAC,
    },
    "Alabama": {
        "cite": "Dept. of Physics and Astronomy, University of Alabama, Tuscaloosa, AL 35487, USA",
        "abbreviation": "UA",
        "is_US": True,
        "region": _US_CAN,
    },
    "Alaska-Anchorage": {
        "cite": "Dept. of Physics and Astronomy, University of Alaska Anchorage, 3211 Providence Dr., Anchorage, AK 99508, USA",
        "abbreviation": "UAA",
        "is_US": True,
        "region": _US_CAN,
    },
    "Alberta": {
        "cite": "Dept. of Physics, University of Alberta, Edmonton, Alberta, Canada T6G 2E1",
        "abbreviation": "ALBERTA",
        "is_US": False,
        "region": _US_CAN,
    },
    "Berlin": {
        "cite": "Institut für Physik, Humboldt-Universität zu Berlin, D-12489 Berlin, Germany",
        "abbreviation": "HUMBOLDT",
        "is_US": False,
        "region": _EUROPE,
    },
    "Bochum": {
        "cite": "Fakultät für Physik & Astronomie, Ruhr-Universität Bochum, D-44780 Bochum, Germany",
        "abbreviation": "BOCHUM",
        "is_US": False,
        "region": _EUROPE,
    },
    "Brussels-ULB": {
        "cite": "Université Libre de Bruxelles, Science Faculty CP230, B-1050 Brussels, Belgium",
        "abbreviation": "ULB",
        "is_US": False,
        "region": _EUROPE,
    },
    "Brussels-VUB": {
        "cite": "Vrije Universiteit Brussel (VUB), Dienst ELEM, B-1050 Brussels, Belgium",
        "abbreviation": "VUB",
        "is_US": False,
        "region": _EUROPE,
    },
    "Canterbury": {
        "cite": "Dept. of Physics and Astronomy, University of Canterbury, Private Bag 4800, Christchurch, New Zealand",
        "abbreviation": "UC",
        "is_US": False,
        "region": _ASIA_PAC,
    },
    "Chiba": {
        "cite": "Dept. of Physics and Institute for Global Prominent Research, Chiba University, Chiba 263-8522, Japan",
        "abbreviation": "CHIBA",
        "is_US": False,
        "region": _ASIA_PAC,
    },
    "Clark-Atlanta": {
        "cite": "CTSPS, Clark-Atlanta University, Atlanta, GA 30314, USA",
        "abbreviation": "CAU",
        "is_US": True,
        "region": _US_CAN,
    },
    "Copenhagen": {
        "cite": "Niels Bohr Institute, University of Copenhagen, DK-2100 Copenhagen, Denmark",
        "abbreviation": "NBI",
        "is_US": False,
        "region": _EUROPE,
    },
    "Delaware": {
        "cite": "Bartol Research Institute and Dept. of Physics and Astronomy, University of Delaware, Newark, DE 19716, USA",
        "abbreviation": "UD",
        "is_US": True,
        "region": _US_CAN,
    },
    "DESY": {
        "cite": "DESY, D-15738 Zeuthen, Germany",
        "abbreviation": "DESY",
        "is_US": False,
        "region": _EUROPE,
    },
    "Dortmund": {
        "cite": "Dept. of Physics, TU Dortmund University, D-44221 Dortmund, Germany",
        "abbreviation": "DTMND",
        "is_US": False,
        "region": _EUROPE,
    },
    "Drexel": {
        "cite": "Dept. of Physics, Drexel University, 3141 Chestnut Street, Philadelphia, PA 19104, USA",
        "abbreviation": "DREXEL",
        "is_US": True,
        "region": _US_CAN,
    },
    "Erlangen": {
        "cite": "Erlangen Centre for Astroparticle Physics, Friedrich-Alexander-Universität Erlangen-Nürnberg, D-91058 Erlangen, Germany",
        "abbreviation": "ERLANGEN",
        "is_US": False,
        "region": _EUROPE,
    },
    "Harvard": {
        "cite": "Department of Physics and Laboratory for Particle Physics and Cosmology, Harvard University, Cambridge, MA 02138, USA",
        "abbreviation": "HARVARD",
        "is_US": True,
        "region": _US_CAN,
    },
    "GaTech": {
        "cite": "School of Physics and Center for Relativistic Astrophysics, Georgia Institute of Technology, Atlanta, GA 30332, USA",
        "abbreviation": "GTECH",
        "is_US": True,
        "region": _US_CAN,
    },
    "Geneva": {
        "cite": "Département de physique nucléaire et corpusculaire, Université de Genève, CH-1211 Genève, Switzerland",
        "abbreviation": "DPNC",
        "is_US": False,
        "region": _EUROPE,
    },
    "Gent": {
        "cite": "Dept. of Physics and Astronomy, University of Gent, B-9True Gent, Belgium",
        "abbreviation": "GENT",
        "is_US": False,
        "region": _EUROPE,
    },
    "Kansas": {
        "cite": "Dept. of Physics and Astronomy, University of Kansas, Lawrence, KS 66045, USA",
        "abbreviation": "KU",
        "is_US": True,
        "region": _US_CAN,
    },
    "Karlsruhe": {
        "cite": "Karlsruhe Institute of Technology, Institut für Kernphysik, D-76021 Karlsruhe, Germany",
        "abbreviation": "KIT",
        "is_US": False,
        "region": _EUROPE,
    },
    "LBNL": {
        "cite": "Lawrence Berkeley National Laboratory, Berkeley, CA 94720, USA",
        "abbreviation": "LBNL",
        "is_US": True,
        "region": _US_CAN,
    },
    "Loyola": {
        "cite": "Department of Physics, Loyola University Chicago, Chicago, IL 60660, USA",
        "abbreviation": "LOYOLA",
        "is_US": True,
        "region": _US_CAN,
    },
    "Mainz": {
        "cite": "Institute of Physics, University of Mainz, Staudinger Weg 7, D-55099 Mainz, Germany",
        "abbreviation": "MAINZ",
        "is_US": False,
        "region": _EUROPE,
    },
    "Marquette": {
        "cite": "Department of Physics, Marquette University, Milwaukee, WI, 53201, USA",
        "abbreviation": "MARQUETTE",
        "is_US": True,
        "region": _US_CAN,
    },
    "Maryland": {
        "cite": "Dept. of Physics, University of Maryland, College Park, MD 20742, USA",
        "abbreviation": "UMD",
        "is_US": True,
        "region": _US_CAN,
    },
    "Mercer": {
        "cite": "Department of Physics, Mercer University, Macon, GA 31207-True1, USA",
        "abbreviation": "MERCER",
        "is_US": True,
        "region": _US_CAN,
    },
    "Michigan-State": {
        "cite": "Dept. of Physics and Astronomy, Michigan State University, East Lansing, MI 48824, USA",
        "abbreviation": "MSU",
        "is_US": True,
        "region": _US_CAN,
    },
    "MIT": {
        "cite": "Dept. of Physics, Massachusetts Institute of Technology, Cambridge, MA 02139, USA",
        "abbreviation": "MIT",
        "is_US": True,
        "region": _US_CAN,
    },
    "Munich": {
        "cite": "Physik-department, Technische Universität München, D-85748 Garching, Germany",
        "abbreviation": "TUM",
        "is_US": False,
        "region": _EUROPE,
    },
    "Munster": {
        "cite": "Institut für Kernphysik, Westfälische Wilhelms-Universität Münster, D-48149 Münster, Germany",
        "abbreviation": "MÜNSTER",
        "is_US": False,
        "region": _EUROPE,
    },
    "Ohio-State-Astronomy": {
        "cite": "Dept. of Astronomy, Ohio State University, Columbus, OH 43210, USA",
        "abbreviation": "OSU",
        "is_US": True,
        "region": _US_CAN,
    },
    "Ohio-State-Physics": {
        "cite": "Dept. of Physics and Center for Cosmology and Astro-Particle Physics, Ohio State University, Columbus, OH 43210, USA",
        "abbreviation": "OSU",
        "is_US": True,
        "region": _US_CAN,
    },
    "Oxford": {
        "cite": "Dept. of Physics, University of Oxford, Parks Road, Oxford OX1 3PU, UK",
        "abbreviation": "UOX",
        "is_US": False,
        "region": _EUROPE,
    },
    "Penn-State-Astronomy": {
        "cite": "Dept. of Astronomy and Astrophysics, Pennsylvania State University, University Park, PA 16802, USA",
        "abbreviation": "PSU",
        "is_US": True,
        "region": _US_CAN,
    },
    "Penn-State-Physics": {
        "cite": "Dept. of Physics, Pennsylvania State University, University Park, PA 16802, USA",
        "abbreviation": "PSU",
        "is_US": True,
        "region": _US_CAN,
    },
    "Rochester": {
        "cite": "Dept. of Physics and Astronomy, University of Rochester, Rochester, NY 14627, USA",
        "abbreviation": "ROCHESTER",
        "is_US": True,
        "region": _US_CAN,
    },
    "SD-Mines-Tech": {
        "cite": "Physics Department, South Dakota School of Mines and Technology, Rapid City, SD 57701, USA",
        "abbreviation": "SDSMT",
        "is_US": True,
        "region": _US_CAN,
    },
    "SNOLAB": {
        "cite": "SNOLAB, 1039 Regional Road 24, Creighton Mine 9, Lively, ON, Canada P3Y 1N2",
        "abbreviation": "QUEEN'S",
        "is_US": False,
        "region": _US_CAN,
    },
    "Southern": {
        "cite": "Dept. of Physics, Southern University, Baton Rouge, LA 70813, USA",
        "abbreviation": "SUBR",
        "is_US": True,
        "region": _US_CAN,
    },
    "Stockholm": {
        "cite": "Oskar Klein Centre and Dept. of Physics, Stockholm University, SE-10691 Stockholm, Sweden",
        "abbreviation": "SU",
        "is_US": False,
        "region": _EUROPE,
    },
    "Stony-Brook": {
        "cite": "Dept. of Physics and Astronomy, Stony Brook University, Stony Brook, NY 11794-3800, USA",
        "abbreviation": "SBU",
        "is_US": True,
        "region": _US_CAN,
    },
    "Sungkyunkwan-Physics": {
        "cite": "Dept. of Physics, Sungkyunkwan University, Suwon 16419, Korea",
        "abbreviation": "SKKU",
        "is_US": False,
        "region": _ASIA_PAC,
    },
    "Sungkyunkwan-Basic-Science": {
        "cite": "Institute of Basic Science, Sungkyunkwan University, Suwon 16419, Korea",
        "abbreviation": "SKKU",
        "is_US": False,
        "region": _ASIA_PAC,
    },
    "Texas-Arlington": {
        "cite": "Dept. of Physics, University of Texas at Arlington, 502 Yates St., Science Hall Rm 108, Box 19059, Arlington, TX 76019, USA",
        "abbreviation": "UTA",
        "is_US": True,
        "region": _US_CAN,
    },
    "UC-Berkeley": {
        "cite": "Dept. of Physics, University of California, Berkeley, CA 94720, USA",
        "abbreviation": "UCB",
        "is_US": True,
        "region": _US_CAN,
    },
    "UC-Irvine": {
        "cite": "Dept. of Physics and Astronomy, University of California, Irvine, CA 92697, USA",
        "abbreviation": "UCI",
        "is_US": True,
        "region": _US_CAN,
    },
    "UCLA": {
        "cite": "Department of Physics and Astronomy, UCLA, Los Angeles, CA 90095, USA",
        "abbreviation": "UCLA",
        "is_US": True,
        "region": _US_CAN,
    },
    "Uppsala": {
        "cite": "Dept. of Physics and Astronomy, Uppsala University, Box 516, S-75120 Uppsala, Sweden",
        "abbreviation": "UU",
        "is_US": False,
        "region": _EUROPE,
    },
    "UW-Madison-Astronomy": {
        "cite": "Dept. of Astronomy, University of Wisconsin–Madison, Madison, WI 53706, USA",
        "abbreviation": "UW",
        "is_US": True,
        "region": _US_CAN,
    },
    "UW-Madison-WIPAC": {
        "cite": "Dept. of Physics and Wisconsin IceCube Particle Astrophysics Center, University of Wisconsin–Madison, Madison, WI 53706, USA",
        "abbreviation": "UW",
        "is_US": True,
        "region": _US_CAN,
    },
    "UW-River-Falls": {
        "cite": "Dept. of Physics, University of Wisconsin, River Falls, WI 54022, USA",
        "abbreviation": "UWRF",
        "is_US": True,
        "region": _US_CAN,
    },
    "Wuppertal": {
        "cite": "Dept. of Physics, University of Wuppertal, D-42119 Wuppertal, Germany",
        "abbreviation": "WUPPERTAL",
        "is_US": False,
        "region": _EUROPE,
    },
    "Yale": {
        "cite": "Dept. of Physics, Yale University, New Haven, CT 06520, USA",
        "abbreviation": "YALE",
        "is_US": True,
        "region": _US_CAN,
    },
}  # type: Dict[str, InstitutionMeta]
