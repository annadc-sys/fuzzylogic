
"""
--------------------
FUZZY FUNCTIONS
--------------------
Collection of general-purpose functions that map a value X onto the
unit-interval [0,1]. These functions work as closures. The inner function uses
the variables of the outer function.

These functions work in two steps: prime and call.
In the first step the function is constructed, initialized and
constants pre-evaluated. In the second step the actual value
is passed into the function, using the arguments of the first step.

Definitions
-----------
These functions are used to determine the *membership* of a value x in a fuzzy-
set. Thus, the 'height' is the variable 'm' in general.
In a normal set there is at least one m with m == 1. This is the default.
In a non-normal set, the global maximum and minimum is skewed.
The following definitions are for normal sets.

The intervals with non-zero m are called 'support', short s_m
The intervals with m == 1 are called 'core', short c_m
The intervals  m != 1 and m != 0 are called 'boundary'.
The intervals with m == 0 are called 'unsupported', short no_m

In a fuzzy set with one and only one m == 1, this element is called 'prototype'.
"""


from math import exp, log, sqrt, isinf, isnan

#####################
# SPECIAL FUNCTIONS #
#####################

def inv(g):
    """Invert the given function within the unit-interval.
    For sets, the ~ operator uses this. It is equivalent to the TRUTH value of FALSE.
    """
    def f(x):
        return 1 - g(x)
    return f


def noop():
    """Do nothing and return the value as is.
    Useful for testing.
    """
    def f(x):
        return x
    return f

def constant(c):
    """Always return the same value, no matter the input.
    Useful for testing.
    >>> f = constant(1)
    >>> f(0)
    1
    """

    def f(x):
        return c
    return f


def alpha(floor, ceiling, func):
    """Function to clip a function.
    This is used to either cut off the upper or lower part of a graph.
    Actually, this is more like a hedge but doesn't make sense for sets.
    """
    assert floor <= ceiling
    assert 0 <= floor
    assert 1 >= ceiling
    
    def f(x):
        if func(x) >= ceiling:
            return ceiling
        elif func(x) <= floor:
            return floor
        else: 
            return func(x)
    return f

########################
# MEMBERSHIP FUNCTIONS #
########################

def singleton(p, *, no_m=0, c_m=1):
    """A single spike.
    >>> f = singleton(2)
    >>> f(1)
    0
    >>> f(2)
    1
    """

    assert 0 <= no_m < c_m <= 1

    def f(x):
        return c_m if x == p else no_m
    return f


def linear(m:float=0, b:float=0) -> callable:
    """A textbook linear function with y-axis section and gradient.
    f(x) = m*x + b
    BUT CLIPPED.

    >>> f = linear(1, -1)
    >>> f(-2)   # should be -3 but clipped
    0
    >>> f(0)    # should be -1 but clipped
    0
    >>> f(1)
    0
    >>> f(1.5)
    0.5
    >>> f(2)
    1
    >>> f(3)    # should be 2 but clipped
    1
    """
    def f(x) -> float:
        y = m * x + b
        if y <= 0:
            return 0
        elif y >= 1:
            return 1
        else:
            return y
    return f


def bounded_linear(low, high, *, c_m=1, no_m=0):
    """Variant of the linear function with gradient being determined by bounds.

    THIS FUNCTION ONLY CAN HAVE A POSITIVE SLOPE -
    USE inv() IF IT NEEDS TO BE NEGATIVE

    The bounds determine minimum and maximum value-mappings,
    but also the gradient. As [0, 1] must be the bounds for y-values,
    left and right bounds specify 2 points on the graph, for which the formula
    f(x) = y = (y2 - y1) / (x2 - x1) * (x - x1) + y1 = (y2 - y1) / (x2 - x1) *
                                                                (x - x2) + y2

    (right_y - left_y) / ((right - left) * (x - self.left) + left_y)
    works.
    
    >>> f = bounded_linear(2, 3)
    >>> f(1)
    0.0
    >>> f(2)
    0.0
    >>> f(2.5)
    0.5
    >>> f(3)
    1.0
    >>> f(4)
    1.0
    """
    assert low < high, "low must be less than high"
    assert c_m > no_m, "core_m must be greater than unsupported_m"

    gradient = (c_m - no_m) / (high - low)
    
    # special cases found by hypothesis
    
    def g_0(x):
        return (c_m + no_m) / 2
    
    if gradient == 0:
        return g_0
    
    def g_inf(x):
        asymptode = (high + low) / 2
        if x < asymptode:
            return no_m
        elif x > asymptode:
            return c_m
        else:
            return (c_m + no_m) / 2
    
    if isinf(gradient):
        return g_inf
    
    def f(x):
        y = gradient * (x - low) + no_m
        if y < 0:
            return 0.
        if y > 1:
            return 1.
        return y
    return f


def R(low, high):
    """Simple alternative for bounded_linear().
    THIS FUNCTION ONLY CAN HAVE A POSITIVE SLOPE -
    USE THE S() FUNCTION FOR NEGATIVE SLOPE.
    """

    assert low < high, "low must be less than high."

    def f(x):
        if x < low:
            return 0
        if low <= x <= high:
            return (x - low) / (high - low)
        if x > high:
            return 1
    return f


def S(low, high):
    """Simple alternative for inv(bounded_linear()
    THIS FUNCTION ONLY CAN HAVE A NEGATIVE SLOPE -
    USE THE R() FUNCTION FOR POSITIVE SLOPE.
    """
    assert low < high, "low must be less than high"

    def f(x):
        if x < low:
            return 1
        if low <= x <= high:
            return (high - x) / (high - low)
        if high < x:
            return 0
    return f


def rectangular(low:float, high:float, *, c_m:float=1, no_m:float=0) -> callable:
    """Basic rectangular function that returns the core_y for the core else 0.
    -----
        ______
        |    |
    ____|    |___
    """

    assert low < high, 'left must be less than right.'

    def f(x:float) -> float:
        if x < low:
            return no_m
        if low <= x <= high:
            return c_m
        if high < x:
            return no_m

    return f


def triangular(low, high, *, c=None, c_m=1, no_m=0):
    """Basic triangular norm as combination of two linear functions.

         /\
    ____/  \___

    """
    assert low < high, 'low must be less than high.'
    assert no_m < c_m
    
    c = c if c is not None else (low + high) / 2.
    assert low < c < high, "peak must be inbetween"
    
    left_slope = bounded_linear(low, c, no_m=0, c_m=c_m)
    right_slope = inv(bounded_linear(c, high, no_m=0, c_m=c_m))

    def f(x):
        return left_slope(x) if x <= c else right_slope(x)
    return f


def trapezoid(low, c_low, c_high, high, *, c_m=1, no_m=0):
    """Combination of rectangular and triangular, for convenience.
          ____
         /    \
    ____/      \___

    """

    assert low < c_low <= c_high < high
    assert 0 <= no_m < c_m <= 1 

    left_slope = bounded_linear(low, c_low, c_m=c_m, no_m=no_m)
    right_slope = inv(bounded_linear(c_high, high, c_m=c_m, no_m=no_m))

    def f(x):
        if x < low or high < x:
            return no_m
        elif x < c_low:
            return left_slope(x)
        elif x > c_high:
            return right_slope(x)
        else:
            return c_m

    return f


def sigmoid(L, k, x0):
    """Special logistic function.

    http://en.wikipedia.org/wiki/Logistic_function

    f(x) = L / (1 + e^(-k*(x-x0)))
    with
    x0 = x-value of the midpoint
    L = the curve's maximum value
    k = steepness
    """
    # need to be really careful here, otherwise we end up in nanland
    assert 0 < L <= 1, 'L invalid.'

    def f(x):
        if isnan(k*x):
            # e^(0*inf) = 1
            o = 1
        else:
            try:
                o = exp(-k*(x - x0))
            except OverflowError:
                o = float("inf")
        return L / (1 + o)

    return f


def bounded_sigmoid(low, high):
    """
    Calculates a weight based on the sigmoid function.

    We specify the lower limit where f(x) = 0.1 and the
    upper with f(x) = 0.9 and calculate the steepness and elasticity
    based on these. We don't need the general logistic function as we
    operate on [0,1].

    USE inv() IF IT NEEDS TO BE NEGATIVE

    vars
    ----
    low: x-value with f(x) = 0.1
    for x < low: m -> 0
    high: x-value with f(x) = 0.9
    for x > high: m -> 1

    >>> f = bounded_sigmoid(0, 1)
    >>> f(0)
    0.1
    >>> round(f(1), 2)
    0.9
    >>> round(f(100000), 2)
    1.0
    >>> round(f(-100000), 2)
    0.0
    """
    assert low < high, 'low must be less than high'
    
    k = -(4. * log(3)) / (low - high)
    # yay for limits! .. and for goddamn hidden divisions by zero thanks to floats >:/
    try:
        o = 9 if isinf(k) else 9 * exp(low * k)
    except OverflowError:
        o = float("inf")
        
    def f(x):
        try:
            return 0.1 if isinf(k) else 1. / (1. + exp(x * -k) * o)
        except OverflowError:
            return 0.0
    return f


def simple_sigmoid(k=0.229756):
    """Sigmoid variant with only one parameter (steepness).

    The midpoint is 0.
    The slope is positive for positive k and negative k.
    f(x) is within [0,1] for any real k and x.
    >>> f = simple_sigmoid()
    >>> round(f(-1000), 2)
    0.0
    >>> f(0)
    0.5
    >>> round(f(1000), 2)
    1.0
    >>> round(f(-20), 2)
    0.01
    >>> round(f(20), 2)
    0.99
    """
    def f(x):
        # yay for limits..
        if (isinf(x) and k == 0):
            return 1/2
        else:
            try:
                return 1 / (1 + exp(x * -k))
            except OverflowError:
                return 0.
    return f


def triangular_sigmoid(low, high, c=None):
    """Version of triangular using sigmoids instead of linear.
    THIS FUNCTION PEAKS AT 0.9

    >>> g = triangular_sigmoid(2, 4)
    >>> g(2)
    0.1
    >>> round(g(3), 2)
    0.9
    """

    assert low < high, "low must be less than high"
    c = c if c is not None else (low + high) / 2.
    assert low < c < high, "c must be inbetween"

    left_slope = bounded_sigmoid(low, c)
    right_slope = inv(bounded_sigmoid(c, high))

    def f(x):
        if x <= c:
            return left_slope(x)
        else:
            return right_slope(x)

    return f


def gauss(c, b, *, c_m=1):
    """Defined by ae^(-b(x-x0)^2), a gaussian distribution.
    Basically a triangular sigmoid function, it comes close to human perception.

    vars
    ----
    c_m (a)
        defines the maximum y-value of the graph
    b
        defines the steepness
    c (x0)
        defines the symmetry center/peak of the graph
    """
    assert 0 < c_m <= 1
    assert 0 < b

    def f(x):
        try:
            o = (x - c)**2
        except OverflowError:
            return 0
        return c_m * exp(-b * o)
    return f


if __name__ == "__main__":
    import doctest
    doctest.testmod()