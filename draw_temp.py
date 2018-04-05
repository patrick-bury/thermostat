import matplotlib.pyplot as plt
import numpy as np
from models import Temperature

status = {
    'OFF': 0,
    'ON': 1,
    '': 0,
    '0': 0
}

mode = {
    '': 0,
    '1': .5,
    '2': 1.5
}

temperatures = Temperature.select().where(Temperature.lieu_id == 1).where(Temperature.date_mesure >= '2018-02-10 00:00:00')
print('End reading database')
x = np.array([data.date_mesure for data in temperatures])
print('End generating X')
y = np.array([data.mesure for data in temperatures])
print('End generating Y')
z = np.array([status[data.chauffage_status] for data in temperatures])
print('End generating Z')
t = np.array([data.mode_confort for data in temperatures if data != ''])
print('End generating T')

fig, ax1 = plt.subplots()
ax1.plot(x, y)
ax1.set_xlabel('Date')
ax1.set_ylabel('Température')

ax2 = ax1.twinx()
ax2.plot(x, z, 'r.')
ax2.set_ylabel('Chauffage (On/Off)')
(xmin, xmax, ymin, ymax) = ax2.axis()
ymin = -.2
ymax = 1.7
ax2.axis((xmin, xmax, ymin, ymax))

ax3 = ax1.twinx()
ax3.plot(x, t, 'g.')
ax3.axis(ax2.axis())
fig.tight_layout()
plt.show()
