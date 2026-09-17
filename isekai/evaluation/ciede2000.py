"""CIEDE2000, the colour-difference formula the hair axis is measured in.

Spelled here rather than pulled in, for the reason the runtime is stdlib-only:
`scikit-image` has `deltaE_ciede2000`, and taking it would pull scipy, networkx,
imageio, tifffile and lazy_loader into the lock for one closed-form function of
six numbers. It is the whole of Sharma, Wu & Dalal (2005), and it is checked
against that paper's own 34-pair reference table in the suite -- which is a
stronger check than trusting a transitive dependency, because the paper's table
was constructed to catch exactly the discontinuities an implementation gets
wrong.

Why this axis is measured at all, and what it may claim: a colour distance means
the same thing in a photograph and in a drawing, so unlike an embedding cosine it
is an **absolute** quantity rather than a within-batch ranking (design.md D1).

The known limitation, stated because it will bite: this is a distance between two
*dominant* colours. Multi-tone hair -- a dark base with a coloured underlayer --
is the norm in this aesthetic, and a render that dropped the underlayer entirely
scores unchanged if the mode did not move (design.md D5). Two of the six subjects
exist to catch that. It is not fixed here.
"""

import math

# The paper's own weighting factors for the graphic-arts reference conditions,
# which is what k_L = k_C = k_H = 1 means. They are parameters in the standard
# and constants here: nothing in this project has a reason to reweight lightness
# against chroma, and a knob nobody turns is a knob that gets turned by accident.
K_L = 1.0
K_C = 1.0
K_H = 1.0

# 25^7, which appears only inside the chroma-dependent `G` term. Precomputed
# because it is a constant the formula spells as an exponent.
_25_POW_7 = 25.0**7

Lab = tuple[float, float, float]


def _mean_hue(h1: float, h2: float, c1: float, c2: float) -> float:
    """Return the mean of two hue angles in degrees, per the standard's rules.

    Hue is circular, so a naive mean puts the average of 350 deg and 10 deg at
    180 -- opposite the colour it should name. The standard handles that by
    folding the difference, and separately defines the mean as the *sum* when
    either chroma is zero: a neutral colour has no hue to average, and letting an
    arbitrary hue angle for black participate would move the answer.
    """
    if c1 * c2 == 0.0:
        return h1 + h2
    difference = abs(h1 - h2)
    if difference <= 180.0:
        return (h1 + h2) / 2.0
    if h1 + h2 < 360.0:
        return (h1 + h2 + 360.0) / 2.0
    return (h1 + h2 - 360.0) / 2.0


def _hue_difference(h1: float, h2: float, c1: float, c2: float) -> float:
    """Return the signed hue difference in degrees, folded into (-180, 180].

    Zero when either chroma is zero, for the same reason as above: there is no
    hue difference between a colour and a neutral, and the arbitrary angle a
    neutral reports would otherwise contribute a real number to the result.
    """
    if c1 * c2 == 0.0:
        return 0.0
    difference = h2 - h1
    if difference > 180.0:
        return difference - 360.0
    if difference < -180.0:
        return difference + 360.0
    return difference


def _hue_angle(b_prime: float, a_prime: float) -> float:
    """Return the hue angle in [0, 360) degrees, with the standard's 0 for neutral."""
    if a_prime == 0.0 and b_prime == 0.0:
        return 0.0
    angle = math.degrees(math.atan2(b_prime, a_prime))
    return angle + 360.0 if angle < 0.0 else angle


def delta_e_2000(first: Lab, second: Lab) -> float:
    """Return the CIEDE2000 colour difference between two CIE L*a*b* colours.

    Symmetric, and zero exactly when the two colours are equal. Larger is more
    different; roughly, a value near 1 is the threshold of a just-noticeable
    difference under reference conditions, which is why this axis is reported as
    a distance and not rescaled into a percentage of anything (design.md D1).
    """
    l1, a1, b1 = first
    l2, a2, b2 = second

    c1_ab = math.hypot(a1, b1)
    c2_ab = math.hypot(a2, b2)
    c_bar_ab = (c1_ab + c2_ab) / 2.0

    # `G` stretches the a* axis for low-chroma colours, which is the correction
    # that makes the formula behave in the blue-grey region the earlier ones did
    # not. It depends on the *mean* chroma of the pair, so it is not a per-colour
    # transform and cannot be precomputed for one side.
    c_bar_pow_7 = c_bar_ab**7
    g = 0.5 * (1.0 - math.sqrt(c_bar_pow_7 / (c_bar_pow_7 + _25_POW_7)))

    a1_prime = (1.0 + g) * a1
    a2_prime = (1.0 + g) * a2
    c1_prime = math.hypot(a1_prime, b1)
    c2_prime = math.hypot(a2_prime, b2)
    h1_prime = _hue_angle(b1, a1_prime)
    h2_prime = _hue_angle(b2, a2_prime)

    delta_l_prime = l2 - l1
    delta_c_prime = c2_prime - c1_prime
    delta_h_deg = _hue_difference(h1_prime, h2_prime, c1_prime, c2_prime)
    delta_h_prime = (
        2.0 * math.sqrt(c1_prime * c2_prime) * math.sin(math.radians(delta_h_deg) / 2.0)
    )

    l_bar_prime = (l1 + l2) / 2.0
    c_bar_prime = (c1_prime + c2_prime) / 2.0
    h_bar_prime = _mean_hue(h1_prime, h2_prime, c1_prime, c2_prime)

    t = (
        1.0
        - 0.17 * math.cos(math.radians(h_bar_prime - 30.0))
        + 0.24 * math.cos(math.radians(2.0 * h_bar_prime))
        + 0.32 * math.cos(math.radians(3.0 * h_bar_prime + 6.0))
        - 0.20 * math.cos(math.radians(4.0 * h_bar_prime - 63.0))
    )

    # The lightness weighting dips around mid-grey, which is where the eye is
    # most sensitive to a lightness change.
    l_offset = (l_bar_prime - 50.0) ** 2
    s_l = 1.0 + (0.015 * l_offset) / math.sqrt(20.0 + l_offset)
    s_c = 1.0 + 0.045 * c_bar_prime
    s_h = 1.0 + 0.015 * c_bar_prime * t

    # The rotation term, which corrects the ellipse orientation in the blue
    # region and is negligible everywhere else.
    c_bar_prime_pow_7 = c_bar_prime**7
    delta_theta = 30.0 * math.exp(-(((h_bar_prime - 275.0) / 25.0) ** 2))
    r_c = 2.0 * math.sqrt(c_bar_prime_pow_7 / (c_bar_prime_pow_7 + _25_POW_7))
    r_t = -r_c * math.sin(math.radians(2.0 * delta_theta))

    lightness = delta_l_prime / (K_L * s_l)
    chroma = delta_c_prime / (K_C * s_c)
    hue = delta_h_prime / (K_H * s_h)

    return math.sqrt(
        lightness * lightness + chroma * chroma + hue * hue + r_t * chroma * hue
    )
