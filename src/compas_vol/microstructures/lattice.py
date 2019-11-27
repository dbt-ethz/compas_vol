import math
from compas.geometry import Frame
from compas.geometry import Point
from compas.geometry import matrix_from_frame
from compas.geometry import matrix_inverse


class Lattice(object):
    """A lattice is defined by it's type, size of a unit cell and its strut diameter.
    Optionally, a frame can be specified to modify orientation and origin.

    Parameters
    ----------
    ltype : int
        The index to the type of lattice.
        A dictionary with indices and corresponding type names can be retrieved with the property `typenames`.
    unitcell : float
        The edgelength of a cubic unit cell.
    thickness : float
        The diameter of the struts.

    Examples
    --------
    >>> from compas_vol.microstructure import Lattice
    >>> lat = Lattice(5, 5.0, 0.3)
    >>> lat.frame = Frame((1, 0, 0), (1, 0.2, 0.1), (-0.3, 1, 0.2))

    """
    def __init__(self, ltype=0, unitcell=1.0, thickness=0.1):
        self.pointlist = self.create_points()
        self.ltypes = self.create_types()
        self._ltype = None
        self.ltype = ltype
        self.unitcell = unitcell
        self.thickness = thickness
        self.frame = Frame.worldXY()

    # ==========================================================================
    # descriptors
    # ==========================================================================

    @property
    def frame(self):
        """Frame: The lattice's frame."""
        return self._frame

    @frame.setter
    def frame(self, frame):
        self._frame = Frame(frame[0], frame[1], frame[2])

    @property
    def ltype(self):
        return self._ltype
    
    @property
    def lattice_type(self):
        return self.ltype, self.typenames[self.ltype]

    @ltype.setter
    def ltype(self, ltype):
        self._ltype = min(max(0, ltype), len(self.ltypes) - 1)

    @property
    def typenames(self):
        tn = ['bigx', 'grid', 'star', 'cross', 'octagon', 'octet', 'vintile', 'dual', 'interlock', 'isotrop', 'hexgrid']
        d = {}
        for i, n in enumerate(tn):
            d[i] = n
        return d

    def create_points(self):
        """
        Creates a list of 20 points (xyz tuples) as possible strut anchors.
        The points are on the vertices (0-7) and edge centres (8-19) of a unit cell octant.
        """
        v1 = 0.0
        v2 = 0.5
        v3 = 0.25
        v4 = 0.20

        points = []

        points.append((v2, v1, v1))  #  1
        points.append((v2, v2, v1))  #  2
        points.append((v1, v1, v1))  #  0
        points.append((v1, v2, v1))  #  3

        points.append((v1, v1, v2))  #  4
        points.append((v2, v1, v2))  #  5
        points.append((v2, v2, v2))  #  6
        points.append((v1, v2, v2))  #  7

        points.append((v3, v1, v1))  #  8
        points.append((v2, v3, v1))  #  9
        points.append((v3, v2, v1))  # 10
        points.append((v1, v3, v1))  # 11

        points.append((v1, v1, v3))  # 12
        points.append((v2, v1, v3))  # 13
        points.append((v2, v2, v3))  # 14
        points.append((v1, v2, v3))  # 15

        points.append((v3, v1, v2))  # 16
        points.append((v2, v3, v2))  # 17
        points.append((v3, v2, v2))  # 18
        points.append((v1, v3, v2))  # 19

        points.append((v4, v1, v1))  # 20
        points.append((v1, v4, v1))  # 21
        points.append((v1, v1, v4))  # 22

        return points

    def create_types(self):
        """
        A lattice type is defined by a list of index tuples.
        The indices refer to `self.pointlist`, generated by `create_points` and specify start and end of each strut.
        """
        bigx = [(0, 6)]
        grid = [(6, 2), (6, 5), (6, 7)]
        star = grid + bigx
        cross = [(1, 6), (3, 6), (4, 6)]
        octagon = [(1, 3), (3, 4), (4, 1)]
        octet = cross + octagon
        vintile = [(8, 13), (13, 17), (17, 18), (18, 15), (15, 11), (11, 8)]
        dual = [(0, 1), (0, 3), (0, 4)]
        interlock = grid+dual
        isotrop = [(0, 1), (2, 1), (5, 1), (7, 1), (3, 7), (6, 7), (4, 7)]
        hexgrid = [(6, 20), (6, 21), (6, 22)]

        types = [bigx, grid, star, cross, octagon, octet, vintile, dual, interlock, isotrop, hexgrid]
        return types

    def get_distance(self, point):
        """
        single point distance function
        """
        if not isinstance(point, Point):
            pt = Point(*point)
        else:
            pt = point
        # frame to frame: box to world
        m = matrix_from_frame(self.frame)
        mi = matrix_inverse(m)
        pt.transform(mi)

        up = [abs((p % self.unitcell) - self.unitcell/2) for p in pt]
        dmin = 9999999.
        for l in self.ltypes[self.ltype]:
            sp = [self.pointlist[l[0]][i] * self.unitcell for i in range(3)]
            ep = [self.pointlist[l[1]][i] * self.unitcell for i in range(3)]
            v = [ep[i]-sp[i] for i in range(3)]
            d = [up[i]-sp[i] for i in range(3)]
            # dot products
            c2 = sum([i*j for (i, j) in zip(v, v)])
            c1 = sum([i*j for (i, j) in zip(d, v)])

            b = c1/c2
            p = [sp[i] + b * v[i] for i in range(3)]
            dmin = min(dmin, sum([(up[i]-p[i])**2 for i in range(3)]))
        return math.sqrt(dmin) - self.thickness/2.0

    def get_distance_numpy(self, x, y, z):
        """
        vectorized distance function
        """
        import numpy as np

        m = matrix_from_frame(self.frame)
        mi = matrix_inverse(m)
        p = np.array([x, y, z, 1])
        md = np.dot(mi, p)
        mg = np.stack(([md[0], md[1], md[2]]), axis=-1)
        mg = abs((mg % self.unitcell) - self.unitcell/2)

        distances = []
        for l in self.ltypes[self.ltype]:
            A = np.array([self.pointlist[l[0]][i] * self.unitcell for i in range(3)])
            B = np.array([self.pointlist[l[1]][i] * self.unitcell for i in range(3)])
            d = np.linalg.norm(np.cross(B-A, mg-A), axis=-1)/np.linalg.norm(B-A)
            distances.append(d)
        return np.asarray(distances).min(axis=0) - self.thickness/2.0


if __name__ == "__main__":
    import numpy as np
    import matplotlib.pyplot as plt

    lat = Lattice(10, 5.0, 0.5)
    lat.frame = Frame((1, 0, 0), (1, 0.2, 0.1), (-0.3, 1, 0.2))

    print(lat.typenames, lat.lattice_type)

    x, y, z = np.ogrid[-14:14:112j, -12:12:96j, -10:10:80j]

    m = lat.get_distance_numpy(x, y, z)

    # num = 200
    # m = np.empty((num, num))
    # for r in range(num):
    #     for c in range(num):
    #         m[r, c] = lat.get_distance((c, r, 10))

    plt.imshow(m[:, :, 25].T, cmap='RdBu')  # transpose because numpy indexing is 1)row 2) column instead of x y
    plt.colorbar()
    plt.axis('equal')
    plt.show()
