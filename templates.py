"""Module 1 — Data Storage & Templates.

Pure data, no tkinter. Holds:
  * ``PLACEHOLDER_FILES``   — placeholder text for the mandatory binary assets
                              (3D models, FMOD audio banks, images).
  * ``CONFIG_TEMPLATES``    — base Kunos-style physics templates with standard
                              ``[HEADER]`` formatting (car, aero, suspensions,
                              engine + supporting files).
  * ``LUT_FILES``           — lookup tables referenced by the templates.
  * ``COMPONENT_LIBRARY``   — the " ADD COMPONENT ▾" template variants
                              (turbos, aero wings, DRS, anti-roll bars, …).
  * ``SUSPENSION_TYPES`` / ``SUSPENSION_TYPE_DEFAULTS`` / ``SLIDER_HINTS``
                            — data driving the specialised suspension editor.

Template strings use ``string.Template`` placeholders (``$car``,
``$screen_name``, ``$brand``, ``$author``, ``$year``) so literal ``{`` braces
(FMOD GUIDs) stay untouched.

Key names and default values follow real extracted Kunos car data
(ks_toyota_gt86, ks_nissan_gtr, abarth500, ks_ferrari_sf15t …).
"""

APP_TITLE = "AC Mod Studio"

# ---------------------------------------------------------------------------
#  Strict AC car folder hierarchy
# ---------------------------------------------------------------------------

REQUIRED_DIRS = (
    "data",
    "sfx",
    "skins/00_default",
    "ui",
)

# ---------------------------------------------------------------------------
#  Placeholder text for mandatory binary files
# ---------------------------------------------------------------------------

_KN5_NOTE = """PLACEHOLDER — $car.kn5 (main 3D model)
=========================================================
Assetto Corsa expects a compiled KN5 model named exactly like the car
folder: content/cars/$car/$car.kn5

Replace this text file with a real model:
  1. Model the car in Blender/3ds Max (Z forward, meters, origin at CoG).
  2. Export FBX and compile with ksEditor (AC SDK) or the Blender
     "Assetto Corsa (.kn5)" community exporter.
  3. Optional LODs use the Kunos naming: $car_LOD_B.kn5, _LOD_C, _LOD_D
     wired up in data/lods.ini.
"""

_COLLIDER_NOTE = """PLACEHOLDER — collider.kn5 (physics collision mesh)
=========================================================
A simplified closed hull of the car body, compiled to KN5 and named
exactly 'collider.kn5'. Keep it low-poly (a boxy shell). The sim will
fail to start a session without a valid collider.
data/colliders.ini must roughly match its dimensions.
"""

_BANK_NOTE = """PLACEHOLDER — $car.bank (FMOD soundbank)
=========================================================
Build with FMOD Studio (project version matching your AC build, community
standard 1.08.x) and the official AC FMOD project template. The bank must
be named exactly '$car.bank'.

Standard event set (under event:/cars/$car/): engine_ext, engine_int,
backfire_ext, backfire_int, gear_ext, gear_int, gear_grind, skid_ext,
skid_int, wheel, wind, bodywork, door, limiter, transmission, turbo.

After building, use FMOD's "Export GUIDs" and update sfx/GUIDs.txt.
"""

_GUIDS_NOTE = """{00000000-0000-0000-0000-000000000000} bank:/$car
{00000000-0000-0000-0000-000000000000} event:/cars/$car/engine_ext
{00000000-0000-0000-0000-000000000000} event:/cars/$car/engine_int
{00000000-0000-0000-0000-000000000000} event:/cars/$car/backfire_ext
{00000000-0000-0000-0000-000000000000} event:/cars/$car/backfire_int
{00000000-0000-0000-0000-000000000000} event:/cars/$car/gear_ext
{00000000-0000-0000-0000-000000000000} event:/cars/$car/gear_int
{00000000-0000-0000-0000-000000000000} event:/cars/$car/gear_grind
{00000000-0000-0000-0000-000000000000} event:/cars/$car/skid_ext
{00000000-0000-0000-0000-000000000000} event:/cars/$car/skid_int
{00000000-0000-0000-0000-000000000000} event:/cars/$car/wheel
{00000000-0000-0000-0000-000000000000} event:/cars/$car/wind
{00000000-0000-0000-0000-000000000000} event:/cars/$car/bodywork
{00000000-0000-0000-0000-000000000000} event:/cars/$car/door
{00000000-0000-0000-0000-000000000000} event:/cars/$car/limiter
{00000000-0000-0000-0000-000000000000} event:/cars/$car/transmission
{00000000-0000-0000-0000-000000000000} event:/cars/$car/turbo
"""

_IMG_NOTE = """PLACEHOLDER — replace with a real image file.
Purpose: $purpose
"""


def _img(purpose: str) -> str:
    return _IMG_NOTE.replace("$purpose", purpose)


PLACEHOLDER_FILES = {
    # -- 3D models ----------------------------------------------------------
    "$car.kn5": _KN5_NOTE,
    "collider.kn5": _COLLIDER_NOTE,
    "driver_base_pos.knh": (
        "PLACEHOLDER — driver_base_pos.knh\n"
        "Driver position blob. Copy one from a similar Kunos car (same\n"
        "seating position) or generate with ksEditor when placing the driver.\n"
    ),
    # -- audio banks --------------------------------------------------------
    "sfx/$car.bank": _BANK_NOTE,
    "sfx/GUIDs.txt": _GUIDS_NOTE,
    # -- images -------------------------------------------------------------
    "logo.png": _img("brand logo copy at the car root, used by in-game "
                     "apps/leaderboards (PNG, square)"),
    "body_shadow.png": _img("baked ambient-occlusion blob shadow under the "
                            "car body"),
    "tyre_0_shadow.png": _img("blob shadow under front-left tyre"),
    "tyre_1_shadow.png": _img("blob shadow under front-right tyre"),
    "tyre_2_shadow.png": _img("blob shadow under rear-left tyre"),
    "tyre_3_shadow.png": _img("blob shadow under rear-right tyre"),
    "skins/00_default/livery.png": _img("small square livery icon shown in "
                                        "the skin list (~64x64 PNG)"),
    "skins/00_default/preview.jpg": _img("launcher preview of this skin "
                                         "(Kunos standard 1022x576 JPG)"),
    "ui/badge.png": _img("brand badge shown on the car page in the launcher "
                         "(~256x256 PNG)"),
    # -- helper note --------------------------------------------------------
    "_README_PLACEHOLDERS.txt": (
        "This car project was generated by AC Mod Studio.\n\n"
        "Every file that should be BINARY (.kn5 models, .bank FMOD audio,\n"
        ".png/.jpg images, .knh driver blob) currently contains placeholder\n"
        "TEXT describing how to produce the real asset. The car will show up\n"
        "in tools but will not drive in the sim until they are replaced.\n\n"
        "The data/ folder contains real, editable Kunos-style physics files\n"
        "— tune them with AC Mod Studio and they work as-is.\n"
    ),
}

# ---------------------------------------------------------------------------
#  Base configuration templates (standard Kunos [HEADER] formatting)
# ---------------------------------------------------------------------------

_CAR_INI = """[HEADER]
VERSION=1\t\t\t\t; version number

[INFO]
SCREEN_NAME=$screen_name

[BASIC]
GRAPHICS_OFFSET=0,-0.35,0\t\t; 3 axis correction (x,y,z), applies only to the 3D object of the car. in meters
GRAPHICS_PITCH_ROTATION=0\t\t; changes 3D object rotation in pitch
TOTALMASS=1285\t\t\t\t; total vehicle weight in kg with driver and no fuel
INERTIA=1.60,1.20,4.60\t\t\t; car polar inertia. Calculated from the car dimensions. Just enter the generic width,height,length

[GRAPHICS]
DRIVEREYES=0.36,1.06,-0.30
ONBOARD_EXPOSURE=19
OUTBOARD_EXPOSURE=31
ON_BOARD_PITCH_ANGLE=-3.0
BONNET_CAMERA_POS=0,0.71,0.40
BUMPER_CAMERA_POS=0,0.71,1.74
MIRROR_POSITION=0.0,1.04,-2.0\t\t; Position used to render the mirror
VIRTUAL_MIRROR_ENABLED=1
USE_ANIMATED_SUSPENSIONS=0
SHAKE_MUL=3\t\t\t\t; Camera onboard G forces multiplier
FUEL_LIGHT_MIN_LITERS=7

[CONTROLS]
FFMULT=2.50\t\t\t\t; force feedback gain multiplier
STEER_ASSIST=1.000
STEER_LOCK=450\t\t\t\t; Real car's steer lock from center to right
STEER_RATIO=-13.0\t\t\t; Steer ratio
LINEAR_STEER_ROD_RATIO=0.0024

[FUEL]
CONSUMPTION=0.0027\t\t\t; fuel consumption. In one second the consumption is (rpm*gas*CONSUMPTION)/1000 litres
FUEL=30\t\t\t\t\t; default starting fuel in litres
MAX_FUEL=50\t\t\t\t; max fuel in litres

[FUELTANK]
POSITION=0,-0.10,-1.45\t\t\t; x,y,z position of the fuel tank relative to the CoG

[RIDE]
PICKUP_FRONT_HEIGHT=-0.285\t\t; Height of the front ride height pickup point in meters
PICKUP_REAR_HEIGHT=-0.285\t\t; Height of the rear ride height pickup point in meters

[RULES]
MIN_HEIGHT=0.0\t\t\t\t; meters min height front/rear

[PIT_STOP]
TYRE_CHANGE_TIME_SEC=10\t\t\t; time spent to change each tyre
FUEL_LITER_TIME_SEC=0.6\t\t\t; time spent to put 1 lt of fuel inside the car
BODY_REPAIR_TIME_SEC=20\t\t\t; time spent to repair 10% of body damage
ENGINE_REPAIR_TIME_SEC=2\t\t; time spent to repair 10% of engine damage
SUSP_REPAIR_TIME_SEC=30\t\t\t; time spent to repair 10% of suspension damage
"""

_ENGINE_INI = """[HEADER]
VERSION=1
POWER_CURVE=power.lut\t\t\t; power curve file
COAST_CURVE=FROM_COAST_REF\t\t; coast curve. can define 3 different options (coast reference, coast values for mathematical curve, coast curve file)

[ENGINE_DATA]
ALTITUDE_SENSITIVITY=0.1\t\t; sensitivity to altitude
INERTIA=0.120\t\t\t\t; engine inertia
LIMITER=7500\t\t\t\t; engine rev limiter. 0 no limiter
LIMITER_HZ=40\t\t\t\t; frequency of engine limiter
MINIMUM=1000\t\t\t\t; idle rpm
DEFAULT_TURBO_ADJUSTMENT=1.00\t\t; DEFAULT turbo adjustment if one or more turbos are cockpit adjustable

[COAST_REF]
RPM=7500\t\t\t\t; rev number reference
TORQUE=90\t\t\t\t; engine braking torque value in Nm at rev number reference
NON_LINEARITY=0\t\t\t\t; coast engine brake from ZERO to TORQUE value at rpm reference. 0=linear, 1=fully exponential

[COAST_DATA]
COAST0=0
COAST1=0
COAST=0.0000015

[DAMAGE]
TURBO_BOOST_THRESHOLD=1.5\t\t; level of TOTAL boost before the engine starts to take damage
TURBO_DAMAGE_K=0\t\t\t; amount of damage per second per (boost - threshold)
RPM_THRESHOLD=7900\t\t\t; RPM at which the engine starts to take damage
RPM_DAMAGE_K=1\t\t\t\t; amount of damage per second per (rpm - threshold)
"""

_SUSPENSIONS_INI = """[HEADER]
VERSION=2

[BASIC]
WHEELBASE=2.40\t\t\t\t; Wheelbase distance in meters
CG_LOCATION=0.52\t\t\t; Front Weight distribution in percentance

[ARB]
FRONT=19000\t\t\t\t; Front antiroll bar stifness. in Nm
REAR=4800\t\t\t\t; Rear antiroll bar stifness. in Nm

[FRONT]
TYPE=DWB\t\t\t\t; Suspension type. DWB Double Wish Bones, STRUT McPherson strut, AXLE live axle, ML multilink
BASEY=-0.15\t\t\t\t; Distance of CG from the center of the wheel in meters. Front Wheel Radius+BASEY=front CoG
TRACK=1.50\t\t\t\t; Track width in meters
RIM_OFFSET=0.037\t\t\t; lateral rim offset in meters
ROD_LENGTH=0.180\t\t\t; push rod length in meters. positive raises ride height, negative lowers ride height
HUB_MASS=27\t\t\t\t; unsprung mass per corner in kg (wheel, tyre, brake, hub)
WBCAR_TOP_FRONT=0.38302,0.12311,0.1348\t\t; Top front car side wishbone attach point
WBCAR_TOP_REAR=0.38302,0.12451,-0.1669\t\t; Top rear car side wishbone attach point
WBCAR_BOTTOM_FRONT=0.4552,-0.0696,-0.0333\t; Bottom front car side wishbone attach point
WBCAR_BOTTOM_REAR=0.4259,-0.08110,-0.39616\t; Bottom rear car side wishbone attach point
WBTYRE_TOP=0.15479,0.10951,-0.0321\t\t; Top tyre side wishbone attach point
WBTYRE_BOTTOM=0.1005,-0.10102,-0.0025\t\t; Bottom tyre side wishbone attach point
WBCAR_STEER=0.4552,-0.0296,0.05890\t\t; Steering rod car side attach point
WBTYRE_STEER=0.0948,-0.06012,0.11691\t\t; Steering rod tyre side attach point
TOE_OUT=-0.00020\t\t\t; Toe-out expressed as the length of the steering arm in meters (negative = toe-in)
STATIC_CAMBER=-0.4\t\t\t; Static Camber in degrees. Actual camber relative to suspension geometry and movement
SPRING_RATE=11708\t\t\t; Wheel rate stifness in N/m. Do not use spring value but calculate the wheel rate
PROGRESSIVE_SPRING_RATE=10000\t\t; progressive spring rate in N/m/m (0 = linear spring)
BUMP_STOP_RATE=50000\t\t\t; bump stop spring rate N/m
BUMPSTOP_UP=0.100\t\t\t; meters to upper bumpstop from the 0 design of the suspension
BUMPSTOP_DN=0.085\t\t\t; meters to bottom bumpstop from the 0 design of the suspension
PACKER_RANGE=0.200\t\t\t; Total suspension movement range, before hitting packers (meters)
DAMP_BUMP=3500\t\t\t\t; Damper wheel rate stifness in N sec/m in compression (slow speed)
DAMP_FAST_BUMP=2100\t\t\t; fast/high-speed compression damping, N sec/m
DAMP_FAST_BUMPTHRESHOLD=0.100\t\t; damper velocity threshold in m/s for fast bump
DAMP_REBOUND=5500\t\t\t; Damper wheel rate stifness in N sec/m in rebound (slow speed)
DAMP_FAST_REBOUND=3500\t\t\t; fast/high-speed rebound damping, N sec/m
DAMP_FAST_REBOUNDTHRESHOLD=0.100\t; damper velocity threshold in m/s for fast rebound

[REAR]
TYPE=DWB
BASEY=-0.15
TRACK=1.50
RIM_OFFSET=0.037
ROD_LENGTH=0.160
HUB_MASS=24.5
WBCAR_TOP_FRONT=0.38302,0.12311,0.1669
WBCAR_TOP_REAR=0.38302,0.12451,-0.1348
WBCAR_BOTTOM_FRONT=0.4259,-0.08110,0.39616
WBCAR_BOTTOM_REAR=0.4552,-0.0696,0.0333
WBTYRE_TOP=0.15479,0.10951,0.0321
WBTYRE_BOTTOM=0.1005,-0.10102,0.0025
WBCAR_STEER=0.4552,-0.0296,-0.05890\t\t; rear steer rod acts as a fixed toe link
WBTYRE_STEER=0.0948,-0.06012,-0.11691
TOE_OUT=-0.00030
STATIC_CAMBER=-1.6
SPRING_RATE=13417
PROGRESSIVE_SPRING_RATE=10000
BUMP_STOP_RATE=61000
BUMPSTOP_UP=0.085
BUMPSTOP_DN=0.085
PACKER_RANGE=0.160
DAMP_BUMP=2600
DAMP_FAST_BUMP=1250
DAMP_FAST_BUMPTHRESHOLD=0.100
DAMP_REBOUND=2600
DAMP_FAST_REBOUND=1300
DAMP_FAST_REBOUNDTHRESHOLD=0.100

[GRAPHICS_OFFSETS]
WHEEL_LF=0\t\t\t\t; Left front graphical offset of the wheel positioning in the x axis (width). + is left - is right
SUSP_LF=0\t\t\t\t; Left front graphical offset of the suspension positioning in the x axis (width)
WHEEL_RF=0
SUSP_RF=0
WHEEL_LR=0
SUSP_LR=0
WHEEL_RR=0
SUSP_RR=0

[DAMAGE]
MIN_VELOCITY=40\t\t\t\t; MINIMUM VELOCITY TO START TAKING DAMAGE (km/h)
GAIN=0.0004\t\t\t\t; AMOUNT OF STEER ROD DEFLECTION FOR IMPACT KMH
MAX_DAMAGE=0.05\t\t\t\t; MAXIMUM AMOUNT OF STEER ROD DEFLECTION ALLOWED (meters)
DEBUG_LOG=0\t\t\t\t; ACTIVATES DAMAGE DEBUG IN THE LOG
"""

_AERO_INI = """[HEADER]
VERSION=2

[WING_0]
NAME=BODY
CHORD=2.20\t\t\t\t; longitudinal length of the wing in meters
SPAN=1.75\t\t\t\t; lateral width of the wing in meters
POSITION=0,0.10,0.20\t\t\t; x,y,z position relative to CoG
LUT_AOA_CL=wing_body_AOA_CL.lut\t\t; angle of attack -> lift coefficient
LUT_GH_CL=\t\t\t\t; ground height -> CL multiplier (optional)
CL_GAIN=1.0
LUT_AOA_CD=wing_body_AOA_CD.lut\t\t; angle of attack -> drag coefficient
LUT_GH_CD=\t\t\t\t; ground height -> CD multiplier (optional)
CD_GAIN=1.0
ANGLE=0\t\t\t\t\t; wing angle in degrees
ZONE_FRONT_CL=0.30\t\t\t; damage sensitivity multipliers per impact zone
ZONE_FRONT_CD=0.35
ZONE_REAR_CL=0.30
ZONE_REAR_CD=0.35
ZONE_LEFT_CL=0.15
ZONE_LEFT_CD=0.10
ZONE_RIGHT_CL=0.15
ZONE_RIGHT_CD=0.10
"""

# ---------------------------------------------------------------------------
#  Lookup tables referenced by the templates
# ---------------------------------------------------------------------------

_POWER_LUT = """0|0
1000|150
2000|230
3000|290
4000|330
5000|350
6000|345
6500|330
7000|305
7500|270
"""

_WING_BODY_CL = """-90|0
-12|-0.10
-6|-0.05
0|0.00
6|-0.02
12|-0.06
90|0
"""

_WING_BODY_CD = """-90|1.20
-12|0.55
-6|0.44
0|0.42
6|0.46
12|0.60
90|1.20
"""

LUT_FILES = {
    "power.lut": _POWER_LUT,
    "wing_body_AOA_CL.lut": _WING_BODY_CL,
    "wing_body_AOA_CD.lut": _WING_BODY_CD,
}

CONFIG_TEMPLATES = {
    "car.ini": _CAR_INI,
    "engine.ini": _ENGINE_INI,
    "suspensions.ini": _SUSPENSIONS_INI,
    "aero.ini": _AERO_INI,
}

# ---------------------------------------------------------------------------
#  ui/ui_car.json and skins/<skin>/ui_skin.json builders
# ---------------------------------------------------------------------------


def build_ui_car_json(car_id: str, screen_name: str, brand: str, *,
                      author: str = "AC Mod Studio", year: int = 2026) -> dict:
    return {
        "name": screen_name,
        "brand": brand,
        "description": (f"{screen_name} — generated with AC Mod Studio.<br>"
                        "<br>Replace this description with the story of "
                        "your car."),
        "tags": ["street", "rwd", "manual", brand.lower()],
        "class": "street",
        "specs": {
            "bhp": "290bhp",
            "torque": "350Nm",
            "weight": "1285kg",
            "topspeed": "250km/h",
            "acceleration": "--s 0-100",
            "pwratio": "4.43kg/hp",
        },
        "torqueCurve": [["0", "0"], ["1000", "150"], ["2000", "230"],
                        ["3000", "290"], ["4000", "330"], ["5000", "350"],
                        ["6000", "345"], ["7000", "305"], ["7500", "270"]],
        "powerCurve": [["0", "0"], ["1000", "21"], ["2000", "65"],
                       ["3000", "122"], ["4000", "186"], ["5000", "246"],
                       ["6000", "291"], ["7000", "300"], ["7500", "285"]],
        "year": year,
        "author": author,
        "version": "1.0",
        "url": "",
    }


def build_ui_skin_json(skin_name: str) -> dict:
    return {
        "skinname": skin_name,
        "drivername": "",
        "country": "",
        "team": "",
        "number": "0",
        "priority": 1,
    }


# ---------------------------------------------------------------------------
#  Suspension editor data
# ---------------------------------------------------------------------------

# Accepted TYPE values in vanilla AC: DWB, STRUT, AXLE, ML (multilink).
SUSPENSION_TYPES = ["DWB", "STRUT", "AXLE", "ML"]

# Default sub-option keys injected when a TYPE is picked in the suspension
# editor. Geometry values come from real cars: DWB = Kunos ks_mazda_mx5_nd2
# front, STRUT = Kunos ks_toyota_gt86 front, AXLE = 4-link muscle-car rear,
# ML = S13 rear multilink.
SUSPENSION_TYPE_DEFAULTS = {
    "DWB": {
        "hint": "Double wishbone — 8 pickup points (WBCAR_*/WBTYRE_*)",
        "keys": {
            "WBCAR_TOP_FRONT": "0.38302,0.12311,0.1348",
            "WBCAR_TOP_REAR": "0.38302,0.12451,-0.1669",
            "WBCAR_BOTTOM_FRONT": "0.4552,-0.0696,-0.0333",
            "WBCAR_BOTTOM_REAR": "0.4259,-0.08110,-0.39616",
            "WBTYRE_TOP": "0.15479,0.10951,-0.0321",
            "WBTYRE_BOTTOM": "0.1005,-0.10102,-0.0025",
            "WBCAR_STEER": "0.4552,-0.0296,0.05890",
            "WBTYRE_STEER": "0.0948,-0.06012,0.11691",
        },
    },
    "STRUT": {
        "hint": "McPherson strut — STRUT_CAR/STRUT_TYRE + lower wishbone",
        "keys": {
            "STRUT_CAR": "0.2459,0.4512,-0.0498",
            "STRUT_TYRE": "0.0881,-0.1182,0.0093",
            "WBCAR_BOTTOM_FRONT": "0.3722,-0.0995,0.308",
            "WBCAR_BOTTOM_REAR": "0.4038,-0.1045,-0.0424",
            "WBTYRE_BOTTOM": "0.0881,-0.1182,0.0093",
            "WBCAR_STEER": "0.5833,-0.0917,-0.1417",
            "WBTYRE_STEER": "0.1088,-0.1182,-0.1304",
        },
    },
    "AXLE": {
        "hint": "Live axle — rigid axle located by links (see [AXLE])",
        "keys": {},
        "sections": {
            "AXLE": {
                "LINK_COUNT": "4",
                "J0_CAR": "0.5588,-0.127,0.5422",
                "J0_AXLE": "0.5588,-0.127,0.0",
                "J1_CAR": "-0.5588,-0.127,0.5422",
                "J1_AXLE": "-0.5588,-0.127,0.0",
                "J2_CAR": "0.2588,0.1,0.6422",
                "J2_AXLE": "0.1288,0.127,0.0",
                "J3_CAR": "-0.2588,0.1,0.6422",
                "J3_AXLE": "-0.1288,0.127,0.0",
                "TORQUE_REACTION": "0.5",
            },
        },
    },
    "ML": {
        "hint": "Multilink — 5 links, JOINT0..JOINT4 (JOINT4 = toe link)",
        "keys": {
            "JOINT0_CAR": "0.24360,0.12500,0.15544",
            "JOINT0_TYRE": "0.07928,0.13139,0.04595",
            "JOINT1_CAR": "0.36277,0.12800,-0.09500",
            "JOINT1_TYRE": "0.05928,0.13639,-0.05000",
            "JOINT2_CAR": "0.22228,0.01168,0.28340",
            "JOINT2_TYRE": "0.06346,-0.10000,0.00000",
            "JOINT3_CAR": "0.34870,-0.07177,0.03300",
            "JOINT3_TYRE": "0.06346,-0.10000,0.00000",
            "JOINT4_CAR": "0.50000,0.00400,-0.12905",
            "JOINT4_TYRE": "0.14932,-0.01100,-0.16511",
        },
    },
}

# Slider ranges for the suspension editor. Keyed by "SECTION/KEY" (wins) or
# plain "KEY". Anything not listed gets a heuristic range from its value.
SLIDER_HINTS = {
    "BASIC/WHEELBASE": (1.5, 4.0),
    "BASIC/CG_LOCATION": (0.30, 0.70),
    "ARB/FRONT": (0, 150000),
    "ARB/REAR": (0, 150000),
    "SPRING_RATE": (0, 250000),
    "PROGRESSIVE_SPRING_RATE": (0, 500000),
    "BUMP_STOP_RATE": (0, 500000),
    "BUMPSTOP_UP": (0, 0.30),
    "BUMPSTOP_DN": (0, 0.30),
    "PACKER_RANGE": (0, 0.50),
    "DAMP_BUMP": (0, 20000),
    "DAMP_FAST_BUMP": (0, 20000),
    "DAMP_FAST_BUMPTHRESHOLD": (0, 0.50),
    "DAMP_REBOUND": (0, 20000),
    "DAMP_FAST_REBOUND": (0, 20000),
    "DAMP_FAST_REBOUNDTHRESHOLD": (0, 0.50),
    "STATIC_CAMBER": (-10.0, 10.0),
    "TOE_OUT": (-0.01, 0.01),
    "TRACK": (0.8, 2.5),
    "BASEY": (-0.50, 0.50),
    "RIM_OFFSET": (-0.20, 0.20),
    "ROD_LENGTH": (-0.30, 0.30),
    "HUB_MASS": (10, 150),
    "DAMAGE/MIN_VELOCITY": (0, 100),
    "DAMAGE/GAIN": (0, 0.01),
    "DAMAGE/MAX_DAMAGE": (0, 0.5),
    "DAMAGE/DEBUG_LOG": (0, 1),
    "TORQUE_REACTION": (0, 1),
    "LINK_COUNT": (2, 5),
}

# ---------------------------------------------------------------------------
#  " ADD COMPONENT ▾" template library
# ---------------------------------------------------------------------------
#  {target filename: {group: {variant: [(section, {key: value}), ...]}}}
#  A section name ending in '#' (TURBO_#, WING_#) is auto-numbered to the
#  next free index; fixed names merge into the existing section.

_TURBO_BASE = {
    "LAG_DN": "0.990", "LAG_UP": "0.994",
    "MAX_BOOST": "1.00", "WASTEGATE": "1.00", "DISPLAY_MAX_BOOST": "1.00",
    "REFERENCE_RPM": "3500", "GAMMA": "2.5", "COCKPIT_ADJUSTABLE": "0",
}

COMPONENT_LIBRARY = {
    "engine.ini": {
        "Turbo": {
            "Street Single Turbo": [
                ("TURBO_#", dict(_TURBO_BASE)),
                ("ENGINE_DATA", {"DEFAULT_TURBO_ADJUSTMENT": "1.00"}),
            ],
            "Race Turbo (cockpit adjustable)": [
                ("TURBO_#", dict(_TURBO_BASE, MAX_BOOST="1.70",
                                 WASTEGATE="1.70", DISPLAY_MAX_BOOST="1.70",
                                 REFERENCE_RPM="3650",
                                 COCKPIT_ADJUSTABLE="1")),
                ("ENGINE_DATA", {"DEFAULT_TURBO_ADJUSTMENT": "1.00"}),
            ],
            "80s F1 Qualifying Turbo": [
                ("TURBO_#", dict(_TURBO_BASE, LAG_DN="0.982", LAG_UP="0.992",
                                 MAX_BOOST="4.25", WASTEGATE="4.25",
                                 DISPLAY_MAX_BOOST="4.25",
                                 REFERENCE_RPM="3350", GAMMA="0.5",
                                 COCKPIT_ADJUSTABLE="1")),
                ("ENGINE_DATA", {"DEFAULT_TURBO_ADJUSTMENT": "0.75"}),
            ],
            "Twin Turbo (pair)": [
                ("TURBO_#", dict(_TURBO_BASE, MAX_BOOST="0.60",
                                 WASTEGATE="0.50", DISPLAY_MAX_BOOST="0.50",
                                 REFERENCE_RPM="2000", GAMMA="2.0")),
                ("TURBO_#", dict(_TURBO_BASE, MAX_BOOST="0.60",
                                 WASTEGATE="0.50", DISPLAY_MAX_BOOST="0.50",
                                 REFERENCE_RPM="2000", GAMMA="2.0")),
            ],
            "Turbo Overboost Damage": [
                ("DAMAGE", {"TURBO_BOOST_THRESHOLD": "1.5",
                            "TURBO_DAMAGE_K": "5"}),
            ],
        },
    },
    "aero.ini": {
        "Aero Wing": {
            "Rear Wing": [
                ("WING_#", {
                    "NAME": "REAR_WING", "CHORD": "0.30", "SPAN": "1.40",
                    "POSITION": "0,0.90,-2.10",
                    "LUT_AOA_CL": "wing_rear_AOA_CL.lut", "LUT_GH_CL": "",
                    "CL_GAIN": "1.0",
                    "LUT_AOA_CD": "wing_rear_AOA_CD.lut", "LUT_GH_CD": "",
                    "CD_GAIN": "1.0", "ANGLE": "6",
                    "ZONE_REAR_CL": "0.9", "ZONE_REAR_CD": "0.9",
                }),
            ],
            "Front Splitter": [
                ("WING_#", {
                    "NAME": "FRONT_SPLITTER", "CHORD": "0.50", "SPAN": "1.60",
                    "POSITION": "0,0.05,1.90",
                    "LUT_AOA_CL": "wing_front_AOA_CL.lut", "LUT_GH_CL": "",
                    "CL_GAIN": "1.0",
                    "LUT_AOA_CD": "wing_front_AOA_CD.lut", "LUT_GH_CD": "",
                    "CD_GAIN": "1.0", "ANGLE": "0",
                    "ZONE_FRONT_CL": "0.9", "ZONE_FRONT_CD": "0.9",
                }),
            ],
            "Car Body Aero": [
                ("WING_#", {
                    "NAME": "BODY", "CHORD": "2.20", "SPAN": "1.75",
                    "POSITION": "0,0.10,0.20",
                    "LUT_AOA_CL": "wing_body_AOA_CL.lut", "LUT_GH_CL": "",
                    "CL_GAIN": "1.0",
                    "LUT_AOA_CD": "wing_body_AOA_CD.lut", "LUT_GH_CD": "",
                    "CD_GAIN": "1.0", "ANGLE": "0",
                    "ZONE_FRONT_CL": "0.30", "ZONE_FRONT_CD": "0.35",
                    "ZONE_REAR_CL": "0.30", "ZONE_REAR_CD": "0.35",
                    "ZONE_LEFT_CL": "0.15", "ZONE_LEFT_CD": "0.10",
                    "ZONE_RIGHT_CL": "0.15", "ZONE_RIGHT_CD": "0.10",
                }),
            ],
        },
        "DRS": {
            "DRS Rear Flap": [
                ("WING_#", {
                    "NAME": "DRS", "CHORD": "0.20", "SPAN": "1.40",
                    "POSITION": "0,0.95,-2.15",
                    "LUT_AOA_CL": "wing_drs_AOA_CL.lut", "LUT_GH_CL": "",
                    "CL_GAIN": "1.0",
                    "LUT_AOA_CD": "wing_drs_AOA_CD.lut", "LUT_GH_CD": "",
                    "CD_GAIN": "1.0", "ANGLE": "8",
                }),
            ],
        },
    },
    "suspensions.ini": {
        "Anti-Roll Bars": {
            "Street (comfort)": [("ARB", {"FRONT": "19000",
                                          "REAR": "4800"})],
            "Sport": [("ARB", {"FRONT": "24700", "REAR": "19800"})],
            "Race (stiff)": [("ARB", {"FRONT": "60000", "REAR": "40000"})],
        },
        "Heave / 3rd Element": {
            "Formula-style front + rear": [
                ("HEAVE_FRONT", {
                    "ROD_LENGTH": "0.015", "SPRING_RATE": "166000",
                    "PROGRESSIVE_SPRING_RATE": "0",
                    "BUMP_STOP_RATE": "165000", "BUMPSTOP_UP": "0.035",
                    "BUMPSTOP_DN": "0.035", "PACKER_RANGE": "0.045",
                    "DAMP_BUMP": "8276", "DAMP_FAST_BUMP": "2262",
                    "DAMP_FAST_BUMPTHRESHOLD": "0.028",
                    "DAMP_REBOUND": "8680", "DAMP_FAST_REBOUND": "4365",
                    "DAMP_FAST_REBOUNDTHRESHOLD": "0.040",
                }),
                ("HEAVE_REAR", {
                    "ROD_LENGTH": "0.015", "SPRING_RATE": "432000",
                    "PROGRESSIVE_SPRING_RATE": "72286",
                    "BUMP_STOP_RATE": "314286", "BUMPSTOP_UP": "0.035",
                    "BUMPSTOP_DN": "0.035", "PACKER_RANGE": "0.045",
                    "DAMP_BUMP": "9900", "DAMP_FAST_BUMP": "4086",
                    "DAMP_FAST_BUMPTHRESHOLD": "0.048",
                    "DAMP_REBOUND": "11550", "DAMP_FAST_REBOUND": "4479",
                    "DAMP_FAST_REBOUNDTHRESHOLD": "0.120",
                }),
            ],
        },
        "Suspension Damage": {
            "Standard": [("DAMAGE", {"MIN_VELOCITY": "40",
                                     "GAIN": "0.0004",
                                     "MAX_DAMAGE": "0.05",
                                     "DEBUG_LOG": "0"})],
        },
    },
}
