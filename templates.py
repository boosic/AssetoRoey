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

[WING_0]\t\t\t\t\t; Wing identifier. A car can have as many wings as necessary
NAME=BODY\t\t\t\t; name of the wing
CHORD=1\t\t\t\t\t; length of the wing in meters
SPAN=1.73\t\t\t\t; width of the wing in meters. both help determine the frontal area of the wing
POSITION=0,0.23,-0.30\t\t\t; position in x,y,z starting from the CoG
LUT_AOA_CL=wing_body_AOA_CL.lut\t\t; Coefficient of Lift lookup table
LUT_GH_CL=\t\t\t\t; Height aero lift multiplier lookup table
CL_GAIN=0\t\t\t\t; Coefficient of Lift multiplier (for easy fine tuning)
LUT_AOA_CD=wing_body_AOA_CD.lut\t\t; Coefficient of drag lookup table
LUT_GH_CD=\t\t\t\t; Height aero drag multiplier table
CD_GAIN=1.0\t\t\t\t; Coefficient of drag multiplier (for easy fine tuning)
ANGLE=1\t\t\t\t\t; Default starting wing angle (degrees)
ZONE_FRONT_CL=0\t\t\t\t; CL=CL/(1.0+ZONE_x_CL*DAMAGE)
ZONE_FRONT_CD=0\t\t\t\t; CD=CD*(1.0+ZONE_x_CD*DAMAGE)
ZONE_REAR_CL=0
ZONE_REAR_CD=0
ZONE_LEFT_CL=0
ZONE_LEFT_CD=0.01
ZONE_RIGHT_CL=0
ZONE_RIGHT_CD=0.01
"""

_DRIVETRAIN_INI = """[HEADER]
VERSION=3

[TRACTION]
TYPE=RWD\t\t\t\t; Wheel drive. Possible options: FWD (Front Wheel Drive), RWD (Rear Wheel Drive), AWD (All Wheel Drive)

[GEARS]
COUNT=6\t\t\t\t\t; forward gears number
GEAR_R=-4.696\t\t\t\t; rear gear ratio
GEAR_1=5.09
GEAR_2=2.99
GEAR_3=2.04
GEAR_4=1.59
GEAR_5=1.29
GEAR_6=1.0
FINAL=2.87\t\t\t\t; final gear ratio

[DIFFERENTIAL]
POWER=0.60\t\t\t\t; differential lock under power. 1.0=100% lock - 0 0% lock
COAST=0.45\t\t\t\t; differential lock under coasting. 1.0=100% lock 0=0% lock
PRELOAD=0\t\t\t\t; preload torque setting

[GEARBOX]
CHANGE_UP_TIME=260\t\t\t; change up time in milliseconds
CHANGE_DN_TIME=270\t\t\t; change down time in milliseconds
AUTO_CUTOFF_TIME=260\t\t\t; Auto cutoff time for upshifts in milliseconds, 0 to disable
SUPPORTS_SHIFTER=1\t\t\t; 1=Car supports shifter, 0=car supports only paddles
VALID_SHIFT_RPM_WINDOW=800\t\t; range window additional to the precise rev matching rpm that permits gear engage
CONTROLS_WINDOW_GAIN=0.4\t\t; multiplayer for gas,brake,clutch pedals that permits gear engage
INERTIA=0.0182\t\t\t\t; gearbox rotating inertia

[CLUTCH]
MAX_TORQUE=300\t\t\t\t; Nm the clutch can transfer

[AUTOCLUTCH]
UPSHIFT_PROFILE=NONE\t\t\t; Name of the profile to use for autoclutch on upshifts
DOWNSHIFT_PROFILE=DOWNSHIFT_PROFILE\t; Same as above for downshifts
USE_ON_CHANGES=1\t\t\t; Use the autoclutch on gear shifts even when autoclutch is set to off
MIN_RPM=1200\t\t\t\t; Minimum rpm for autoclutch engadgement
MAX_RPM=1800\t\t\t\t; Maximum rpm for autoclutch engadgement
FORCED_ON=0

[DOWNSHIFT_PROFILE]
POINT_0=50\t\t\t\t; Time to reach fully depress clutch
POINT_1=280\t\t\t\t; Time to start releasing clutch
POINT_2=600\t\t\t\t; Time to reach fully released clutch

[AUTOBLIP]
ELECTRONIC=0\t\t\t\t; If =1 then it is a feature of the car and cannot be disabled
POINT_0=20\t\t\t\t; Time to reach full level
POINT_1=140\t\t\t\t; Time to start releasing gas
POINT_2=200\t\t\t\t; Time to reach 0 gas
LEVEL=0.8\t\t\t\t; Gas level to be reached

[DAMAGE]
RPM_WINDOW_K=100

[AUTO_SHIFTER]
UP=7200
DOWN=3500
SLIP_THRESHOLD=0.95
GAS_CUTOFF_TIME=0.300
"""

_BRAKES_INI = """[HEADER]
VERSION=1

[DATA]
MAX_TORQUE=2500\t\t\t\t; Maximum Brake torque in Nm
FRONT_SHARE=0.75\t\t\t; Percentance of brake torque at front axis
HANDBRAKE_TORQUE=1000
COCKPIT_ADJUSTABLE=0\t\t\t; 0: no bias control from cockpit, 1: bias control from cockpit
ADJUST_STEP=0.5\t\t\t\t; step for bias cockpit adjustment
"""

_ELECTRONICS_INI = """[ABS]
SLIP_RATIO_LIMIT=0.11\t\t\t; Slipratio limit before ABS engages
CURVE=\t\t\t\t\t; Slipratio lookup table for multiple ABS levels. Leave blank for a single level
PRESENT=1\t\t\t\t; 1 if present in car, 0 if not present
ACTIVE=1\t\t\t\t; 1 will make the car start with ABS active
RATE_HZ=250\t\t\t\t; ABS pulse frequency

[TRACTION_CONTROL]
SLIP_RATIO_LIMIT=0.11\t\t\t; Slipratio limit before TC engages
CURVE=\t\t\t\t\t; e.g. CURVE=tc_curve.lut for multi-level TC
PRESENT=1
ACTIVE=1
RATE_HZ=170\t\t\t\t; TC pulse frequency
MIN_SPEED_KMH=35\t\t\t; TC automatically OFF under this speed
"""

_COLLIDERS_INI = """[COLLIDER_0]
CENTRE=0,-0.26,0.05\t\t\t; x,y,z of box centre, metres, relative to model origin
SIZE=1.57,0.08,3.30\t\t\t; width, height, length of box in metres
GROUND_ENABLE=1\t\t\t\t; box collides with the ground
"""

_TYRES_INI = """[HEADER]
VERSION=10\t\t\t\t; final AC tyre model (AC 1.14+)

[VIRTUALKM]
USE_LOAD=1

[COMPOUND_DEFAULT]
INDEX=0\t\t\t\t\t; default compound index

[FRONT]
NAME=Street
SHORT_NAME=ST
WIDTH=0.205\t\t\t\t; tyre width in meters
RADIUS=0.30815\t\t\t\t; tyre radius in meters
RIM_RADIUS=0.2286\t\t\t; rim radius in meters (use 1 inch more than nominal)
ANGULAR_INERTIA=1.65\t\t\t; angular inertia of front rim+tyre+brake disc together
DAMP=500\t\t\t\t; Damping rate of front tyre in N sec/m
RATE=233568\t\t\t\t; Spring rate of front tyres in N/m
WEAR_CURVE=street_front.lut\t\t; lookup table (vkm | grip%)
SPEED_SENSITIVITY=0.003601
RELAXATION_LENGTH=0.07137
ROLLING_RESISTANCE_0=10\t\t\t; rolling resistance constant component
ROLLING_RESISTANCE_1=0.000973\t\t; rolling resistance velocity (squared) component
ROLLING_RESISTANCE_SLIP=4668\t\t; rolling resistance slip angle component
FLEX=0.001113\t\t\t\t; tire profile flex. bigger number = more flex
CAMBER_GAIN=0.110\t\t\t; Camber gain value as slipangle multiplayer
DCAMBER_0=1.1
DCAMBER_1=-13\t\t\t\t; D=D*(1.0 - (camberRAD*DCAMBER_0 + camberRAD^2 * DCAMBER_1))
FRICTION_LIMIT_ANGLE=8.88\t\t; Slip angle peak (degrees)
XMU=0.28
PRESSURE_STATIC=29\t\t\t; STATIC (COLD) PRESSURE, psi
PRESSURE_SPRING_GAIN=7364\t\t; INCREASE IN N/m per psi (from 26psi reference)
PRESSURE_FLEX_GAIN=0.45\t\t\t; INCREASE IN FLEX per psi
PRESSURE_RR_GAIN=0.55\t\t\t; INCREASE IN RR RESISTENCE per psi
PRESSURE_D_GAIN=0.004\t\t\t; loss of tyre footprint with pressure rise
PRESSURE_IDEAL=35\t\t\t; Ideal pressure for grip, psi
FZ0=2517\t\t\t\t; reference load N
LS_EXPY=0.8243\t\t\t\t; lateral load-sensitivity exponent
LS_EXPX=0.8914\t\t\t\t; longitudinal load-sensitivity exponent
DX_REF=1.26\t\t\t\t; longitudinal friction coeff at FZ0
DY_REF=1.23\t\t\t\t; lateral friction coeff at FZ0
FLEX_GAIN=0.0311
FALLOFF_LEVEL=0.87\t\t\t; grip fraction far past the peak
FALLOFF_SPEED=4
CX_MULT=1.02
RADIUS_ANGULAR_K=0.01\t\t\t; Radius grows in MILLIMETERS with angular velocity
BRAKE_DX_MOD=0.05

[REAR]
NAME=Street
SHORT_NAME=ST
WIDTH=0.205
RADIUS=0.30815
RIM_RADIUS=0.2286
ANGULAR_INERTIA=1.65
DAMP=500
RATE=233568
WEAR_CURVE=street_rear.lut
SPEED_SENSITIVITY=0.003601
RELAXATION_LENGTH=0.07137
ROLLING_RESISTANCE_0=10
ROLLING_RESISTANCE_1=0.000973
ROLLING_RESISTANCE_SLIP=4668
FLEX=0.001113
CAMBER_GAIN=0.110
DCAMBER_0=1.1
DCAMBER_1=-13
FRICTION_LIMIT_ANGLE=8.88
XMU=0.28
PRESSURE_STATIC=29
PRESSURE_SPRING_GAIN=7364
PRESSURE_FLEX_GAIN=0.45
PRESSURE_RR_GAIN=0.55
PRESSURE_D_GAIN=0.004
PRESSURE_IDEAL=35
FZ0=2517
LS_EXPY=0.8243
LS_EXPX=0.8914
DX_REF=1.26
DY_REF=1.23
FLEX_GAIN=0.0311
FALLOFF_LEVEL=0.87
FALLOFF_SPEED=4
CX_MULT=1.02
RADIUS_ANGULAR_K=0.01
BRAKE_DX_MOD=0.05

[THERMAL_FRONT]
SURFACE_TRANSFER=0.0140\t\t\t; How fast external sources heat the tread: 0-1
PATCH_TRANSFER=0.00027\t\t\t; heat transfer between tyre locations: 0-1
CORE_TRANSFER=0.00049\t\t\t; tyre tread to inner air
INTERNAL_CORE_TRANSFER=0.0057
FRICTION_K=0.06001\t\t\t; Quantity of slip becoming heat
ROLLING_K=0.23\t\t\t\t; rolling resistance heat
PERFORMANCE_CURVE=tcurve_street.lut\t; temperature/grip lut
GRAIN_GAMMA=1
GRAIN_GAIN=0.4
BLISTER_GAMMA=1
BLISTER_GAIN=0.4
COOL_FACTOR=2.51
SURFACE_ROLLING_K=1.15054

[THERMAL_REAR]
SURFACE_TRANSFER=0.0140
PATCH_TRANSFER=0.00027
CORE_TRANSFER=0.00049
INTERNAL_CORE_TRANSFER=0.0057
FRICTION_K=0.06001
ROLLING_K=0.23
PERFORMANCE_CURVE=tcurve_street.lut
GRAIN_GAMMA=1
GRAIN_GAIN=0.4
BLISTER_GAMMA=1
BLISTER_GAIN=0.4
COOL_FACTOR=2.51
SURFACE_ROLLING_K=1.15054
"""

_AI_INI = """[HEADER]
VERSION=3

[GEARS]
UP=7200\t\t\t\t\t; AI upshift rpm
DOWN=4000\t\t\t\t; AI downshift rpm
SLIP_THRESHOLD=0.95
GAS_CUTOFF_TIME=0.300

[PEDALS]
GASGAIN=4.0
BRAKE_HINT=1.06
TRAIL_HINT=1

[STEER]
STEER_GAIN=1.67

[LOOKAHEAD]
BASE=18.5
GAS_BRAKE_LOOKAHEAD=0

[ULTRA_GRIP]
VALUE=1.2

[PHYSICS_HINTS]
AERO_HINT=1
"""

_LODS_INI = """[COCKPIT_HR]
DISTANCE_SWITCH=7\t\t\t; metres: swap to low-res cockpit beyond this

[DRIVER_HR]
DISTANCE_SWITCH=25

[LOD_0]
FILE=$car.kn5
IN=0
OUT=2000
"""

_DRIVER3D_INI = """[MODEL]
NAME=driver_no_HANS\t\t\t; driver 3D model from content/driver
POSITION=0.36,0.09,-0.23\t\t; driver model position relative to the car

[STEER_ANIMATION]
NAME=steer.ksanim\t\t\t; steering animation clip in animations/
LOCK=360\t\t\t\t; degrees of steering wheel rotation covered by the clip
"""

_FUEL_CONS_INI = """[FUEL_EVAL]
KM_PER_LITER=9.5\t\t\t; used by AI/strategy fuel estimates
"""

_SETUP_INI = """[DISPLAY_METHOD]
SHOW_CLICKS=1

/////////////////////////////////////////////////////
;TYRES
/////////////////////////////////////////////////////

[PRESSURE_LF]
SHOW_CLICKS=0
TAB=TYRES
NAME=Pressure LF
MIN=15
MAX=40
STEP=1
POS_X=0
POS_Y=2
HELP=HELP_LF_PRESSURE

[PRESSURE_RF]
SHOW_CLICKS=0
TAB=TYRES
NAME=Pressure RF
MIN=15
MAX=40
STEP=1
POS_X=1
POS_Y=2
HELP=HELP_RF_PRESSURE

[PRESSURE_LR]
SHOW_CLICKS=0
TAB=TYRES
NAME=Pressure LR
MIN=15
MAX=40
STEP=1
POS_X=0
POS_Y=3
HELP=HELP_LR_PRESSURE

[PRESSURE_RR]
SHOW_CLICKS=0
TAB=TYRES
NAME=Pressure RR
MIN=15
MAX=40
STEP=1
POS_X=1
POS_Y=3
HELP=HELP_RR_PRESSURE

/////////////////////////////////////////////////////
;ALIGNMENT
/////////////////////////////////////////////////////

[CAMBER_LF]
SHOW_CLICKS=0
TAB=ALIGNMENT
NAME=Camber LF
MIN=-4.0
MAX=0.5
STEP=1
POS_X=0
POS_Y=0
HELP=HELP_LF_CAMBER

[CAMBER_RF]
SHOW_CLICKS=0
TAB=ALIGNMENT
NAME=Camber RF
MIN=-4.0
MAX=0.5
STEP=1
POS_X=1
POS_Y=0
HELP=HELP_RF_CAMBER

[CAMBER_LR]
SHOW_CLICKS=0
TAB=ALIGNMENT
NAME=Camber LR
MIN=-4.0
MAX=0.5
STEP=1
POS_X=0
POS_Y=1
HELP=HELP_LR_CAMBER

[CAMBER_RR]
SHOW_CLICKS=0
TAB=ALIGNMENT
NAME=Camber RR
MIN=-4.0
MAX=0.5
STEP=1
POS_X=1
POS_Y=1
HELP=HELP_RR_CAMBER

[TOE_OUT_LF]
SHOW_CLICKS=2
TAB=ALIGNMENT
NAME=Toe LF
MIN=-60
MAX=70
STEP=10
POS_X=0
POS_Y=2
HELP=HELP_LF_TOE

[TOE_OUT_RF]
SHOW_CLICKS=2
TAB=ALIGNMENT
NAME=Toe RF
MIN=-60
MAX=70
STEP=10
POS_X=1
POS_Y=2
HELP=HELP_RF_TOE

/////////////////////////////////////////////////////
;GENERIC
/////////////////////////////////////////////////////

[FUEL]
SHOW_CLICKS=0
TAB=GENERIC
NAME=Fuel
MIN=5
MAX=50
STEP=1
POS_X=0.5
POS_Y=0
HELP=HELP_FUEL

[BRAKE_POWER_MULT]
SHOW_CLICKS=0
TAB=GENERIC
NAME=Brake power
MIN=80
MAX=100
STEP=1
POS_X=0.5
POS_Y=1
HELP=HELP_BRAKE_POWER_MULT
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
7800|0
"""

# Road-car body aero (values follow Kunos ks_mazda_mx5_nd2)
_WING_BODY_CL = """-10|-0.20
-2|-0.035
0|-0.030
2|-0.025
5|-0.015
8|-0.008
10|0
30|0
"""

_WING_BODY_CD = """-10|1
-2|0.47
0|0.46
2|0.48
5|0.49
8|0.50
10|0.52
30|1
"""

# Formula-style front wing (Kunos SDK formula_k)
_WING_FRONT_CL = """-10|-0.4
0|0.34
4|0.42
8|0.50
12|0.58
16|0.66
17|0.68
18|0.64
19|0.60
20|0.55
"""

_WING_FRONT_CD = """-10|1
0|0.1
4|0.108
8|0.116
12|0.124
16|0.132
17|0.140
18|0.147
19|0.153
20|0.160
"""

# Formula-style rear wing with stall past 17 degrees (Kunos SDK formula_k)
_WING_REAR_CL = """-10|-0.4
0|0.22
2|0.29
4|0.360
6|0.430
8|0.500
10|0.570
12|0.640
14|0.71
16|0.780
17|0.815
18|0.780
19|0.700
20|0.600
"""

_WING_REAR_CD = """-10|1
0|0.15
2|0.16
4|0.17
6|0.18
8|0.19
10|0.20
12|0.21
14|0.22
16|0.23
17|0.24
18|0.30
19|0.35
20|0.40
"""

# DRS-style movable flap: produces load only once deployed past ~3 degrees
_WING_MOVABLE_CL = """-10|-0.1
0|0
3|0
6|0.10
9|0.18
12|0.26
16|0.35
20|0.30
"""

_WING_MOVABLE_CD = """-10|0.2
0|0.01
3|0.01
6|0.03
9|0.05
12|0.07
16|0.10
20|0.14
"""

_WING_DIFFUSER_CL = """-10|0
-1|0.05
0|0.18
1|0.192
2|0.190
5|0.170
8|0.100
10|0.05
12|0.0
"""

_WING_DIFFUSER_CD = """-10|0
0|0
12|0
"""

# Ground-height multipliers: downforce rises as the car gets lower,
# dies when the surface touches the ground
_HEIGHT_FRONTWING_CL = """0|0
0.010|1.25
0.040|1.10
0.050|1.05
0.060|1.00
0.070|0.95
0.080|0.9
0.090|0.7
0.120|0.4
"""

_HEIGHT_FRONTWING_CD = """0|0.970
0.030|0.985
0.060|1.006
0.120|1.010
"""

_HEIGHT_DIFFUSER_CL = """0|0
0.010|1.15
0.020|1.1
0.030|1.05
0.040|1.0
0.050|0.95
0.070|0.90
0.080|0.4
"""

_HEIGHT_DIFFUSER_CD = """0|0.970
0.030|0.985
0.060|1.006
0.120|1.010
"""

# Airbrake controller tables: +5 deg past 30% brake, gated above 60 km/h
_CONTROLLER_BRAKE = """0|0
0.29|0
0.3|5
1|5
"""

_CONTROLLER_SPEED = """0|0
60|0
61|1
"""

# Tyre wear (virtual km -> grip %) and thermal (temp C -> grip multiplier)
_WEAR_STREET = """0|100
30|99.8
60|99.6
100|99.4
300|98.5
600|97.5
1000|96.5
"""

_TCURVE_STREET = """-20|0.85
0|0.89
20|0.95
50|0.99
75|1.00
90|1.00
110|0.98
130|0.92
150|0.85
"""

LUT_FILES = {
    "power.lut": _POWER_LUT,
    "wing_body_AOA_CL.lut": _WING_BODY_CL,
    "wing_body_AOA_CD.lut": _WING_BODY_CD,
    "wing_front_AOA_CL.lut": _WING_FRONT_CL,
    "wing_front_AOA_CD.lut": _WING_FRONT_CD,
    "wing_rear_AOA_CL.lut": _WING_REAR_CL,
    "wing_rear_AOA_CD.lut": _WING_REAR_CD,
    "wing_rearmovable_AOA_CL.lut": _WING_MOVABLE_CL,
    "wing_rearmovable_AOA_CD.lut": _WING_MOVABLE_CD,
    "wing_diffuser_AOA_CL.lut": _WING_DIFFUSER_CL,
    "wing_diffuser_AOA_CD.lut": _WING_DIFFUSER_CD,
    "height_frontwing_CL.lut": _HEIGHT_FRONTWING_CL,
    "height_frontwing_CD.lut": _HEIGHT_FRONTWING_CD,
    "height_diffuser_CL.lut": _HEIGHT_DIFFUSER_CL,
    "height_diffuser_CD.lut": _HEIGHT_DIFFUSER_CD,
    "wing_controller_brake.lut": _CONTROLLER_BRAKE,
    "wing_controller_speed.lut": _CONTROLLER_SPEED,
    "street_front.lut": _WEAR_STREET,
    "street_rear.lut": _WEAR_STREET,
    "tcurve_street.lut": _TCURVE_STREET,
}

CONFIG_TEMPLATES = {
    # The four core templates
    "car.ini": _CAR_INI,
    "engine.ini": _ENGINE_INI,
    "suspensions.ini": _SUSPENSIONS_INI,
    "aero.ini": _AERO_INI,
    # The rest of the minimum set a drivable AC car needs
    "drivetrain.ini": _DRIVETRAIN_INI,
    "tyres.ini": _TYRES_INI,
    "brakes.ini": _BRAKES_INI,
    "electronics.ini": _ELECTRONICS_INI,
    "colliders.ini": _COLLIDERS_INI,
    "ai.ini": _AI_INI,
    "lods.ini": _LODS_INI,
    "driver3d.ini": _DRIVER3D_INI,
    "setup.ini": _SETUP_INI,
    "fuel_cons.ini": _FUEL_CONS_INI,
    # Kunos SDK sample ships these zero-byte: an EMPTY drs.ini keeps DRS
    # disabled (any non-empty drs.ini enables it). Populate them via the
    # " ADD COMPONENT ▾" DRS / Wing Animation templates.
    "drs.ini": "",
    "wing_animations.ini": "",
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
                    "NAME": "REAR", "CHORD": "1", "SPAN": "1.0",
                    "POSITION": "0,0.15,-1.186",
                    "LUT_AOA_CL": "wing_rear_AOA_CL.lut", "LUT_GH_CL": "",
                    "CL_GAIN": "1.0",
                    "LUT_AOA_CD": "wing_rear_AOA_CD.lut", "LUT_GH_CD": "",
                    "CD_GAIN": "1.0", "ANGLE": "6",
                    "ZONE_FRONT_CL": "0", "ZONE_FRONT_CD": "0",
                    "ZONE_REAR_CL": "0.01", "ZONE_REAR_CD": "0.01",
                    "ZONE_LEFT_CL": "0", "ZONE_LEFT_CD": "0",
                    "ZONE_RIGHT_CL": "0", "ZONE_RIGHT_CD": "0",
                }),
            ],
            "Front Wing / Splitter (ground effect)": [
                ("WING_#", {
                    "NAME": "FRONT", "CHORD": "1", "SPAN": "1.0",
                    "POSITION": "0,-0.215,1.700",
                    "LUT_AOA_CL": "wing_front_AOA_CL.lut",
                    "LUT_GH_CL": "height_frontwing_CL.lut",
                    "CL_GAIN": "1.0",
                    "LUT_AOA_CD": "wing_front_AOA_CD.lut",
                    "LUT_GH_CD": "height_frontwing_CD.lut",
                    "CD_GAIN": "1.0", "ANGLE": "6",
                    "ZONE_FRONT_CL": "0.01", "ZONE_FRONT_CD": "0.01",
                    "ZONE_REAR_CL": "0", "ZONE_REAR_CD": "0",
                    "ZONE_LEFT_CL": "0", "ZONE_LEFT_CD": "0",
                    "ZONE_RIGHT_CL": "0", "ZONE_RIGHT_CD": "0",
                }),
            ],
            "Diffuser (ground effect)": [
                ("WING_#", {
                    "NAME": "DIFFUSER", "CHORD": "1", "SPAN": "1.0",
                    "POSITION": "0,-0.25,-1.18",
                    "LUT_AOA_CL": "wing_diffuser_AOA_CL.lut",
                    "LUT_GH_CL": "height_diffuser_CL.lut",
                    "CL_GAIN": "1.0",
                    "LUT_AOA_CD": "wing_diffuser_AOA_CD.lut",
                    "LUT_GH_CD": "height_diffuser_CD.lut",
                    "CD_GAIN": "1.0", "ANGLE": "0",
                    "ZONE_REAR_CL": "0.01", "ZONE_REAR_CD": "0.01",
                }),
            ],
            "Car Body Aero": [
                ("WING_#", {
                    "NAME": "BODY", "CHORD": "1", "SPAN": "1.73",
                    "POSITION": "0,0.23,-0.30",
                    "LUT_AOA_CL": "wing_body_AOA_CL.lut", "LUT_GH_CL": "",
                    "CL_GAIN": "0",
                    "LUT_AOA_CD": "wing_body_AOA_CD.lut", "LUT_GH_CD": "",
                    "CD_GAIN": "1.0", "ANGLE": "1",
                    "ZONE_FRONT_CL": "0", "ZONE_FRONT_CD": "0",
                    "ZONE_REAR_CL": "0", "ZONE_REAR_CD": "0",
                    "ZONE_LEFT_CL": "0", "ZONE_LEFT_CD": "0.01",
                    "ZONE_RIGHT_CL": "0", "ZONE_RIGHT_CD": "0.01",
                }),
            ],
        },
        "DRS": {
            "DRS Movable Rear Flap": [
                # The flap-only loads live in the rearmovable LUTs (zero
                # below 3 deg). Enable DRS itself in data/drs.ini with a
                # [WING_N] matching this wing's index.
                ("WING_#", {
                    "NAME": "REAR_MOVABLE", "CHORD": "1", "SPAN": "1.0",
                    "POSITION": "0,0.15,-1.186",
                    "LUT_AOA_CL": "wing_rearmovable_AOA_CL.lut",
                    "LUT_GH_CL": "",
                    "CL_GAIN": "1.0",
                    "LUT_AOA_CD": "wing_rearmovable_AOA_CD.lut",
                    "LUT_GH_CD": "",
                    "CD_GAIN": "1.0", "ANGLE": "12",
                    "ZONE_REAR_CL": "0.01", "ZONE_REAR_CD": "0.01",
                }),
            ],
        },
        "Active Aero": {
            "Airbrake (brake + speed controllers)": [
                ("DYNAMIC_CONTROLLER_#", {
                    "WING": "1", "COMBINATOR": "ADD", "INPUT": "BRAKE",
                    "LUT": "wing_controller_brake.lut", "FILTER": "0.90",
                    "UP_LIMIT": "6", "DOWN_LIMIT": "0",
                }),
                ("DYNAMIC_CONTROLLER_#", {
                    "WING": "1", "COMBINATOR": "MULT", "INPUT": "SPEED_KMH",
                    "LUT": "wing_controller_speed.lut", "FILTER": "0.90",
                    "UP_LIMIT": "6", "DOWN_LIMIT": "0",
                }),
            ],
        },
    },
    "drs.ini": {
        "DRS": {
            "F1-style (track DRS zones)": [
                ("HEADER", {"VERSION": "1"}),
                # WING_1 must match the movable wing's index in aero.ini
                ("WING_1", {"MODE": "ANGLE", "EFFECT": "0.1", "ANGLE": "0"}),
                ("DEACTIVATION", {"LIMIT_G": "6.9"}),
            ],
            "Road car (usable anywhere)": [
                ("HEADER", {"VERSION": "1"}),
                ("WING_1", {"MODE": "EFFECT", "EFFECT": "0.1",
                            "ANGLE": "0"}),
                ("DRS_ZONES", {"IGNORE_ZONES": "1"}),
                ("DEACTIVATION", {"LIMIT_G": "6.9"}),
            ],
        },
    },
    "wing_animations.ini": {
        "Wing Animation": {
            "DRS flap animation": [
                ("HEADER", {"VERSION": "2"}),
                ("ANIMATION_#", {"WING": "1", "FILE": "wing_rear.ksanim",
                                 "MIN": "0", "MAX": "16"}),
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
    "drivetrain.ini": {
        "Differential": {
            "Open diff": [("DIFFERENTIAL", {"POWER": "0", "COAST": "0",
                                            "PRELOAD": "0"})],
            "Street LSD": [("DIFFERENTIAL", {"POWER": "0.60", "COAST": "0.45",
                                             "PRELOAD": "0"})],
            "Race LSD (preloaded)": [("DIFFERENTIAL", {"POWER": "0.75",
                                                       "COAST": "0.60",
                                                       "PRELOAD": "60"})],
        },
        "Traction": {
            "RWD": [("TRACTION", {"TYPE": "RWD"})],
            "FWD": [("TRACTION", {"TYPE": "FWD"})],
            "AWD (with front share)": [
                ("TRACTION", {"TYPE": "AWD"}),
                ("AWD", {"FRONT_SHARE": "0.40"}),
            ],
        },
    },
    "electronics.ini": {
        "Driver Aids": {
            "Street ABS + TC": [
                ("ABS", {"SLIP_RATIO_LIMIT": "0.11", "CURVE": "",
                         "PRESENT": "1", "ACTIVE": "1", "RATE_HZ": "250"}),
                ("TRACTION_CONTROL", {"SLIP_RATIO_LIMIT": "0.11",
                                      "CURVE": "", "PRESENT": "1",
                                      "ACTIVE": "1", "RATE_HZ": "170",
                                      "MIN_SPEED_KMH": "35"}),
            ],
            "No assists (race)": [
                ("ABS", {"PRESENT": "0", "ACTIVE": "0"}),
                ("TRACTION_CONTROL", {"PRESENT": "0", "ACTIVE": "0"}),
            ],
            "Electronic Diff Lock (EDL)": [
                ("EDL", {"PRESENT": "1", "ACTIVE": "1",
                         "MAX_SPIN_POWER": "0.8", "MAX_SPIN_COAST": "0.4",
                         "BRAKE_TORQUE_POWER": "50",
                         "BRAKE_TORQUE_COAST": "400",
                         "DEAD_ZONE_POWER": "0.2",
                         "DEAD_ZONE_COAST": "0.0"}),
            ],
        },
    },
}
