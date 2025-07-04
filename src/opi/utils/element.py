from opi.models.string_enum import StringEnum


class Element(StringEnum):
    """
    Class that stores a list of all elements.
    When an element is required as an input, it is to be selected from this class to avoid user error
    """

    # /// HYDROGEN
    HYDROGEN = "H"
    H = "H"
    # /// HELIUM
    HELIUM = "He"
    HE = "He"
    # /// LITHIUM
    LITHIUM = "Li"
    LI = "Li"
    # /// BERYLLIUM
    BERYLLIUM = "Be"
    BE = "Be"
    # /// BORON
    BORON = "B"
    B = "B"
    # /// CARBON
    CARBON = "C"
    C = "C"
    # /// NITROGEN
    NITROGEN = "N"
    N = "N"
    # /// OXYGEN
    OXYGEN = "O"
    O = "O"  # noqa: E741
    # /// FLUORINE
    FLUORINE = "F"
    F = "F"
    # /// NEON
    NEON = "Ne"
    NE = "Ne"
    # /// SODIUM
    SODIUM = "Na"
    NA = "Na"
    # /// MAGNESIUM
    MAGNESIUM = "Mg"
    MG = "Mg"
    # /// ALUMINUM
    ALUMINUM = "Al"
    AL = "Al"
    # /// SILICON
    SILICON = "Si"
    SI = "Si"
    # /// PHOSPHORUS
    PHOSPHORUS = "P"
    P = "P"
    # /// SULFUR
    SULFUR = "S"
    S = "S"
    # /// CHLORINE
    CHLORINE = "Cl"
    CL = "Cl"
    # /// ARGON
    ARGON = "Ar"
    AR = "Ar"
    # /// POTASSIUM
    POTASSIUM = "K"
    K = "K"
    # /// CALCIUM
    CALCIUM = "Ca"
    CA = "Ca"
    # /// SCANDIUM
    SCANDIUM = "Sc"
    SC = "Sc"
    # /// TITANIUM
    TITANIUM = "Ti"
    TI = "Ti"
    # /// VANADIUM
    VANADIUM = "V"
    V = "V"
    # /// CHROMIUM
    CHROMIUM = "Cr"
    CR = "Cr"
    # /// MANGANESE
    MANGANESE = "Mn"
    MN = "Mn"
    # /// IRON
    IRON = "Fe"
    FE = "Fe"
    # /// COBALT
    COBALT = "Co"
    CO = "Co"
    # /// NICKEL
    NICKEL = "Ni"
    NI = "Ni"
    # /// COPPER
    COPPER = "Cu"
    CU = "Cu"
    # /// ZINC
    ZINC = "Zn"
    ZN = "Zn"
    # /// GALLIUM
    GALLIUM = "Ga"
    GA = "Ga"
    # /// GERMANIUM
    GERMANIUM = "Ge"
    GE = "Ge"
    # /// ARSENIC
    ARSENIC = "As"
    AS = "As"
    # /// SELENIUM
    SELENIUM = "Se"
    SE = "Se"
    # /// BROMINE
    BROMINE = "Br"
    BR = "Br"
    # /// KRYPTON
    KRYPTON = "Kr"
    KR = "Kr"
    # /// RUBIDIUM
    RUBIDIUM = "Rb"
    RB = "Rb"
    # /// STRONTIUM
    STRONTIUM = "Sr"
    SR = "Sr"
    # /// YTTRIUM
    YTTRIUM = "Y"
    Y = "Y"
    # /// ZIRCONIUM
    ZIRCONIUM = "Zr"
    ZR = "Zr"
    # /// NIOBIUM
    NIOBIUM = "Nb"
    NB = "Nb"
    # /// MOLYBDENUM
    MOLYBDENUM = "Mo"
    MO = "Mo"
    # /// TECHNETIUM
    TECHNETIUM = "Tc"
    TC = "Tc"
    # /// RUTHENIUM
    RUTHENIUM = "Ru"
    RU = "Ru"
    # /// RHODIUM
    RHODIUM = "Rh"
    RH = "Rh"
    # /// PALLADIUM
    PALLADIUM = "Pd"
    PD = "Pd"
    # /// SILVER
    SILVER = "Ag"
    AG = "Ag"
    # /// CADMIUM
    CADMIUM = "Cd"
    CD = "Cd"
    # /// INDIUM
    INDIUM = "In"
    IN = "In"
    # /// TIN
    TIN = "Sn"
    SN = "Sn"
    # /// ANTIMONY
    ANTIMONY = "Sb"
    SB = "Sb"
    # /// TELLURIUM
    TELLURIUM = "Te"
    TE = "Te"
    # /// IODINE
    IODINE = "I"
    I = "I"  # noqa: E741
    # /// XENON
    XENON = "Xe"
    XE = "Xe"
    # /// CESIUM
    CESIUM = "Cs"
    CS = "Cs"
    # /// BARIUM
    BARIUM = "Ba"
    BA = "Ba"
    # /// LANTHANUM
    LANTHANUM = "La"
    LA = "La"
    # /// CERIUM
    CERIUM = "Ce"
    CE = "Ce"
    # /// PRASEODYMIUM
    PRASEODYMIUM = "Pr"
    PR = "Pr"
    # /// NEODYMIUM
    NEODYMIUM = "Nd"
    ND = "Nd"
    # /// PROMETHIUM
    PROMETHIUM = "Pm"
    PM = "Pm"
    # /// SAMARIUM
    SAMARIUM = "Sm"
    SM = "Sm"
    # /// EUROPIUM
    EUROPIUM = "Eu"
    EU = "Eu"
    # /// GADOLINIUM
    GADOLINIUM = "Gd"
    GD = "Gd"
    # /// TERBIUM
    TERBIUM = "Tb"
    TB = "Tb"
    # /// DYSPROSIUM
    DYSPROSIUM = "Dy"
    DY = "Dy"
    # /// HOLMIUM
    HOLMIUM = "Ho"
    HO = "Ho"
    # /// ERBIUM
    ERBIUM = "Er"
    ER = "Er"
    # /// THULIUM
    THULIUM = "Tm"
    TM = "Tm"
    # /// YTTERBIUM
    YTTERBIUM = "Yb"
    YB = "Yb"
    # /// LUTETIUM
    LUTETIUM = "Lu"
    LU = "Lu"
    # /// HAFNIUM
    HAFNIUM = "Hf"
    HF = "Hf"
    # /// TANTALUM
    TANTALUM = "Ta"
    TA = "Ta"
    # /// WOLFRAM
    WOLFRAM = "W"
    W = "W"
    # /// RHENIUM
    RHENIUM = "Re"
    RE = "Re"
    # /// OSMIUM
    OSMIUM = "Os"
    OS = "Os"
    # /// IRIDIUM
    IRIDIUM = "Ir"
    IR = "Ir"
    # /// PLATINUM
    PLATINUM = "Pt"
    PT = "Pt"
    # /// GOLD
    GOLD = "Au"
    AU = "Au"
    # /// MERCURY
    MERCURY = "Hg"
    HG = "Hg"
    # /// THALLIUM
    THALLIUM = "Tl"
    TL = "Tl"
    # /// LEAD
    LEAD = "Pb"
    PB = "Pb"
    # /// BISMUTH
    BISMUTH = "Bi"
    BI = "Bi"
    # /// POLONIUM
    POLONIUM = "Po"
    PO = "Po"
    # /// ASTATINE
    ASTATINE = "At"
    AT = "At"
    # /// RADON
    RADON = "Rn"
    RN = "Rn"
    # /// FRANCIUM
    FRANCIUM = "Fr"
    FR = "Fr"
    # /// RADIUM
    RADIUM = "Ra"
    RA = "Ra"
    # /// ACTINIUM
    ACTINIUM = "Ac"
    AC = "Ac"
    # /// THORIUM
    THORIUM = "Th"
    TH = "Th"
    # /// PROTACTINIUM
    PROTACTINIUM = "Pa"
    PA = "Pa"
    # /// URANIUM
    URANIUM = "U"
    U = "U"
    # /// NEPTUNIUM
    NEPTUNIUM = "Np"
    NP = "Np"
    # /// PLUTONIUM
    PLUTONIUM = "Pu"
    PU = "Pu"
    # /// AMERICIUM
    AMERICIUM = "Am"
    AM = "Am"
    # /// CURIUM
    CURIUM = "Cm"
    CM = "Cm"
    # /// BERKELIUM
    BERKELIUM = "Bk"
    BK = "Bk"
    # /// CALIFORNIUM
    CALIFORNIUM = "Cf"
    CF = "Cf"
    # /// EINSTEINIUM
    EINSTEINIUM = "Es"
    ES = "Es"
    # /// FERMIUM
    FERMIUM = "Fm"
    FM = "Fm"
    # /// MENDELEVIUM
    MENDELEVIUM = "Md"
    MD = "Md"
    # /// NOBELIUM
    NOBELIUM = "No"
    NO = "No"
    # /// LAWRENCIUM
    LAWRENCIUM = "Lr"
    LR = "Lr"
    # /// RUTHERFORDIUM
    RUTHERFORDIUM = "Rf"
    RF = "Rf"
    # /// DUBNIUM
    DUBNIUM = "Db"
    DB = "Db"
    # /// SEABORGIUM
    SEABORGIUM = "Sg"
    SG = "Sg"
    # /// BOHRIUM
    BOHRIUM = "Bh"
    BH = "Bh"
    # /// HASSIUM
    HASSIUM = "Hs"
    HS = "Hs"
    # /// MEITNERIUM
    MEITNERIUM = "Mt"
    MT = "Mt"
    # /// DARMSTADTIUM
    DARMSTADTIUM = "Ds"
    DS = "Ds"
    # /// ROENTGENIUM
    ROENTGENIUM = "Rg"
    RG = "Rg"
    # /// COPERNICIUM
    COPERNICIUM = "Cn"
    CN = "Cn"
    # /// NIHONIUM
    NIHONIUM = "Nh"
    NH = "Nh"
    # /// FLEROVIUM
    FLEROVIUM = "Fl"
    FL = "Fl"
    # /// MOSCOVIUM
    MOSCOVIUM = "Mc"
    MC = "Mc"
    # /// LIVERMORIUM
    LIVERMORIUM = "Lv"
    LV = "Lv"
    # /// TENNESSINE
    TENNESSINE = "Ts"
    TS = "Ts"
    # /// OGANESSON
    OGANESSON = "Og"
    OG = "Og"

    @classmethod
    def from_atomic_number(cls, atomic_number: int) -> "Element":
        """
        Get element from its atomic number.

        atomic_number: int, allowed range: 1 <= atomic_number <= 118
            Atomic number of the element

        Returns
        -------
        Element
            Returns the corresponding element

        Raises
        ------
        ValueError: Is raised if atomic number is out of range.
        """
        match atomic_number:
            case 1:
                return cls.HYDROGEN
            case 2:
                return cls.HELIUM
            case 3:
                return cls.LITHIUM
            case 4:
                return cls.BERYLLIUM
            case 5:
                return cls.BORON
            case 6:
                return cls.CARBON
            case 7:
                return cls.NITROGEN
            case 8:
                return cls.OXYGEN
            case 9:
                return cls.FLUORINE
            case 10:
                return cls.NEON
            case 11:
                return cls.SODIUM
            case 12:
                return cls.MAGNESIUM
            case 13:
                return cls.ALUMINUM
            case 14:
                return cls.SILICON
            case 15:
                return cls.PHOSPHORUS
            case 16:
                return cls.SULFUR
            case 17:
                return cls.CHLORINE
            case 18:
                return cls.ARGON
            case 19:
                return cls.POTASSIUM
            case 20:
                return cls.CALCIUM
            case 21:
                return cls.SCANDIUM
            case 22:
                return cls.TITANIUM
            case 23:
                return cls.VANADIUM
            case 24:
                return cls.CHROMIUM
            case 25:
                return cls.MANGANESE
            case 26:
                return cls.IRON
            case 27:
                return cls.COBALT
            case 28:
                return cls.NICKEL
            case 29:
                return cls.COPPER
            case 30:
                return cls.ZINC
            case 31:
                return cls.GALLIUM
            case 32:
                return cls.GERMANIUM
            case 33:
                return cls.ARSENIC
            case 34:
                return cls.SELENIUM
            case 35:
                return cls.BROMINE
            case 36:
                return cls.KRYPTON
            case 37:
                return cls.RUBIDIUM
            case 38:
                return cls.STRONTIUM
            case 39:
                return cls.YTTRIUM
            case 40:
                return cls.ZIRCONIUM
            case 41:
                return cls.NIOBIUM
            case 42:
                return cls.MOLYBDENUM
            case 43:
                return cls.TECHNETIUM
            case 44:
                return cls.RUTHENIUM
            case 45:
                return cls.RHODIUM
            case 46:
                return cls.PALLADIUM
            case 47:
                return cls.SILVER
            case 48:
                return cls.CADMIUM
            case 49:
                return cls.INDIUM
            case 50:
                return cls.TIN
            case 51:
                return cls.ANTIMONY
            case 52:
                return cls.TELLURIUM
            case 53:
                return cls.IODINE
            case 54:
                return cls.XENON
            case 55:
                return cls.CESIUM
            case 56:
                return cls.BARIUM
            case 57:
                return cls.LANTHANUM
            case 58:
                return cls.CERIUM
            case 59:
                return cls.PRASEODYMIUM
            case 60:
                return cls.NEODYMIUM
            case 61:
                return cls.PROMETHIUM
            case 62:
                return cls.SAMARIUM
            case 63:
                return cls.EUROPIUM
            case 64:
                return cls.GADOLINIUM
            case 65:
                return cls.TERBIUM
            case 66:
                return cls.DYSPROSIUM
            case 67:
                return cls.HOLMIUM
            case 68:
                return cls.ERBIUM
            case 69:
                return cls.THULIUM
            case 70:
                return cls.YTTERBIUM
            case 71:
                return cls.LUTETIUM
            case 72:
                return cls.HAFNIUM
            case 73:
                return cls.TANTALUM
            case 74:
                return cls.WOLFRAM
            case 75:
                return cls.RHENIUM
            case 76:
                return cls.OSMIUM
            case 77:
                return cls.IRIDIUM
            case 78:
                return cls.PLATINUM
            case 79:
                return cls.GOLD
            case 80:
                return cls.MERCURY
            case 81:
                return cls.THALLIUM
            case 82:
                return cls.LEAD
            case 83:
                return cls.BISMUTH
            case 84:
                return cls.POLONIUM
            case 85:
                return cls.ASTATINE
            case 86:
                return cls.RADON
            case 87:
                return cls.FRANCIUM
            case 88:
                return cls.RADIUM
            case 89:
                return cls.ACTINIUM
            case 90:
                return cls.THORIUM
            case 91:
                return cls.PROTACTINIUM
            case 92:
                return cls.URANIUM
            case 93:
                return cls.NEPTUNIUM
            case 94:
                return cls.PLUTONIUM
            case 95:
                return cls.AMERICIUM
            case 96:
                return cls.CURIUM
            case 97:
                return cls.BERKELIUM
            case 98:
                return cls.CALIFORNIUM
            case 99:
                return cls.EINSTEINIUM
            case 100:
                return cls.FERMIUM
            case 101:
                return cls.MENDELEVIUM
            case 102:
                return cls.NOBELIUM
            case 103:
                return cls.LAWRENCIUM
            case 104:
                return cls.RUTHERFORDIUM
            case 105:
                return cls.DUBNIUM
            case 106:
                return cls.SEABORGIUM
            case 107:
                return cls.BOHRIUM
            case 108:
                return cls.HASSIUM
            case 109:
                return cls.MEITNERIUM
            case 110:
                return cls.DARMSTADTIUM
            case 111:
                return cls.ROENTGENIUM
            case 112:
                return cls.COPERNICIUM
            case 113:
                return cls.NIHONIUM
            case 114:
                return cls.FLEROVIUM
            case 115:
                return cls.MOSCOVIUM
            case 116:
                return cls.LIVERMORIUM
            case 117:
                return cls.TENNESSINE
            case 118:
                return cls.OGANESSON
            case _:
                raise ValueError(f"Atomic number {atomic_number} out of range: 1 <= x <= 118")
