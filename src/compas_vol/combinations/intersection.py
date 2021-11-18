class Intersection(object):
    """The Boolean intersection between two or more volumetric objects.

    Parameters
    ----------
    a: single volumetric object or list of objects
        First object if the intersection is of two objects only. If a is a list of objects, b is discarded.
    b: (optional) volumetric object
        Second object if the intersection is of two objects only.

    Examples
    --------
    >>> s = Sphere(Point(5, 6, 0), 9)
    >>> b = Box(Frame.worldXY(), 20, 15, 10)
    >>> vs = VolSphere(s)
    >>> vb = VolBox(b, 2.5)
    >>> i = Intersection(vs, vb)
    """
    def __init__(self, a=None, b=None):
        if type(a) == list:
            self.objs = a
        else:
            self.objs = [a, b]

    def __repr__(self):
        obj_strings = [str(o) for o in self.objs]
        return 'Intersection([{}])'.format(', '.join(obj_strings))

    def get_distance(self, point):
        """
        single point distance function
        """
        ds = [o.get_distance(point) for o in self.objs]
        return max(ds)

    def get_distance_numpy(self, x, y, z):
        """
        vectorized distance function
        """
        import numpy as np

        distances = ([o.get_distance_numpy(x, y, z) for o in self.objs])
        return np.maximum.reduce(distances)
