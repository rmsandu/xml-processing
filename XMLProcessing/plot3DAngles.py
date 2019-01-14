from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
import numpy as np

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
p = np.array([[-43.11150999, -118.14365791, -1100.99389988],
                [-27.97693445,-124.54828379, -1089.54038197],
                [-55.99892873, -120.42384095, -1084.32576297],
                [-40.75143664, -133.41566716, -1077.33745869],

              [-43.2165748, -34.770722, -1030.85272686],
              [-27.89568594, -43.06953117, -1021.03437003],
              [-56.072327, -44.66085799, -1019.15166512],
              [-40.75143814, -52.95966716, -1009.3333083]])

ax.scatter3D(p[:, 0], p[:, 1], p[:, 2])

x = np.array([[-43.11150999], [-27.97693445], [-55.99892873], [-40.75143664], [-43.2165748],[-27.89568594],[-56.072327],[-40.75143814]])
y = np.array([[-118.14365791], [-124.54828379], [-120.42384095], [-133.41566716], [-34.770722],[-43.06953117],[-44.66085799],[-52.95966716]])
z = np.array([[-1100.99389988], [-1089.54038197], [-1084.32576297], [-1077.33745869], [-1030.85272686],[-1021.03437003],[-1019.15166512],[-1009.3333083]])

labels = ['PT-EP-1n', 'PT-EP-2n', 'PT-EP-3n', 'PT-EP-4n', 'PT-TP-1n','PT-TP-2n','PT-TP-3n','PT-TP-4n']

x = x.flatten()
y = y.flatten()
z = z.flatten()

ax.scatter(x, y, z)
#give the labels to each point
for x, y, z, label in zip(x, y,z, labels):
    ax.text(x, y, z, label)

verts = [[p[0],p[1],p[2],p[3]],
          [p[1],p[2],p[6],p[5]],
          [p[2],p[3],p[7],p[6]],
          [p[3],p[0],p[4],p[7]],
          [p[0],p[1],p[5],p[4]],
          [p[4],p[5],p[6],p[7]]]

collection = Poly3DCollection(verts, linewidths=1, edgecolors='black', alpha=0.2, zsort='min')
face_color = "salmon"
collection.set_facecolor(face_color)
ax.add_collection3d(collection)

plt.show()