import math
from shapely.geometry import Point
from shapely.affinity import scale, rotate

#input parameters
A = Point(1, 1)
B = Point(4, 5)
R = 1

d = A.distance(B)

#first, rotate B to B' around A so that |AB'| = |AB| and B'.y = A.y
#and then take S as midpoint of AB'
S = Point(A.x + d/2, A.y)

#alpha represents the angle of this rotation
alpha = math.atan2(B.y - A.y, B.x - A.x)

#create a circle with center at S passing through A and B'
C = S.buffer(d/2)

#rescale this circle in y-direction so that the corresponding
#axis is R units long
C = scale(C, 1, R/(d/2))

#rotate the ellipse obtained in previous step around A into the
#original position (positive angles represent counter-clockwise rotation)
C = rotate(C, alpha, origin = A, use_radians = True)

for x,y in C.exterior.coords:
    print(x, y)