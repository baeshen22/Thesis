# Camera / lighting presets. Local metres, +Y = north. sun = (azimuth deg from N, elevation deg)
import math as _m
_C = (708.69, -425.33); _R = 1171.03          # frontage arc (from DWG)
def arcpt(a, dr=0.0, z=0.0):
    return (_C[0] + (_R + dr) * _m.cos(a), _C[1] + (_R + dr) * _m.sin(a), z)

GOLD = dict(sun=(288, 11), sun_color=(1.0, 0.74, 0.50), sun_strength=3.6, sky_strength=0.20, air=1.3, exposure=-0.1)
DAY = dict(sun=(250, 38), sun_color=(1.0, 0.93, 0.85), sun_strength=3.4, sky_strength=0.24, air=1.0)
DUSK = dict(sun=(288, 1.5), sun_color=(1.0, 0.55, 0.30), sun_strength=0.9, sky_strength=0.42, air=1.6,
            interior=2.0, led=6.0, exposure=0.55)
def V(base, **kw):
    d = dict(base); d.update(kw); return d

VIEWS = {
    'hero_aerial':   V(GOLD, cam=(-640, -480, 235), look=(-70, 25, 0), lens=30),
    'dusk_aerial':   V(DUSK, cam=arcpt(2.80, 240, 170), look=(-40, -60, 0), lens=26),
    'masterplan':    V(DAY, cam=(0, -5, 1500), look=(0, -4.99, 0), ortho=1000, sun=(215, 55)),
    'arrival':       V(GOLD, cam=arcpt(2.86, 170, 60), look=arcpt(2.79, -150, 0), lens=30),
    'showroom_blvd': V(GOLD, cam=arcpt(2.70, 34, 26), look=arcpt(2.585, -28, 5), lens=30, sun=(292, 14)),
    'arcade':        V(GOLD, cam=(-217.5, 154.7, 1.6), look=(-246.4, 106.7, 2.4), lens=20, sun=(275, 20), clear_people=7, clear_cars=9),
    'arena_hero':    V(GOLD, cam=(-430, -330, 55), look=(-230, -150, 12), lens=30),
    'offroad':       V(GOLD, cam=(140, 76, 25), look=(30, 172, 2), lens=26, sun=(240, 20)),
    'club_ext':      V(DUSK, cam=(-28, -86, 14), look=(-132, -30, 8), lens=30),
    'vision_aerial': V(GOLD, cam=arcpt(2.40, 230, 290), look=(-110, -60, 0), lens=28, sun=(300, 13)),
    'facade_a':      V(GOLD, cam=arcpt(2.40, 4, 5.5), look=arcpt(2.40, -40, 6), lens=32, sun=(292, 18), hide=['palms_', 'shrubs_']),
    'facade_b':      V(GOLD, cam=arcpt(2.55, 4, 5.5), look=arcpt(2.55, -40, 6), lens=32, sun=(292, 18), hide=['palms_', 'shrubs_']),
    'facade_c':      V(GOLD, cam=arcpt(2.95, 4, 5.5), look=arcpt(2.95, -40, 6), lens=32, sun=(292, 18), hide=['palms_', 'shrubs_']),
    'facade_d':      V(GOLD, cam=arcpt(3.015, 4, 5.5), look=arcpt(3.015, -40, 6), lens=32, sun=(292, 18), hide=['palms_', 'shrubs_']),
    'frontage_dusk': V(DUSK, cam=arcpt(2.985, 50, 14), look=(-300, -150, 7), lens=28, interior=3.0, clear_cars=12),
    'showroom_street': V(GOLD, cam=arcpt(2.80, -8.5, 2.2), look=arcpt(2.735, -23, 4.2), lens=24, sun=(292, 16), clear_cars=11, clear_people=8),
    'launch_plaza':  V(GOLD, cam=(-345, -290, 24), look=(-265, -195, 4), lens=28, led=3.0),
}
