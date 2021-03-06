import requests
import io
import zipfile
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection

"""
Funció align_yaxis_np utilitzada per alinear els dos eixos Y. Obtinguda de la URL https://stackoverflow.com/a/41259922
"""
def align_yaxis_np(ax1, ax2):
	"""Align zeros of the two axes, zooming them out by same ratio"""
	axes = np.array([ax1, ax2])
	extrema = np.array([ax.get_ylim() for ax in axes])
	tops = extrema[:,1] / (extrema[:,1] - extrema[:,0])
	# Ensure that plots (intervals) are ordered bottom to top:
	if tops[0] > tops[1]:
		axes, extrema, tops = [a[::-1] for a in (axes, extrema, tops)]
	# How much would the plot overflow if we kept current zoom levels?
	tot_span = tops[1] + 1 - tops[0]
	extrema[0,1] = extrema[0,0] + tot_span * (extrema[0,1] - extrema[0,0])
	extrema[1,0] = extrema[1,1] + tot_span * (extrema[1,0] - extrema[1,1])
	[axes[i].set_ylim(*extrema[i]) for i in range(2)]

aDates= []			# Valor DATA FI (Eix X)
aIA14 = []			# Valor IA14 (Eix Y1)
aVelIA14 = []		# Velocitat variació IA14 (Eix Y2)
aPromVelIA14 = []	# Mitjana velocitat variació IA14 (Eix Y2)
aAccelIA14 = []		# Acceleració variacio IA14
aSegments = []
aColors = []

lLlegenda = (((0.1215, 0.46, 0.7058), "Evolució IA14"),
			((1, 0, 0), "Velocitat IA14 (accel. > 0)"),
			((0, 1, 0), "Velocitat IA14 (accel. < 0)"),
			((0.2, 0.2, 0.2), "Mitjana velocitat IA14"))

lLinRefIA14 = ((25, (0.756862745, 0.988235294, 0.690196078), "IA14 25"),
			 (50, (0.964705882, 0.894117647, 0.666666667), "IA14 50"),
			 (150, (0.964705882, 0.760784314, 0.384313725), "IA14 150"),
			 (250, (0.901960784, 0.356862745, 0.262745098), "IA14 250"))

# Descàrrega del fitxer ZIP
sURL = "https://dadescovid.cat/static/csv/catalunya_setmanal_total_pob.zip"
print ("Obtenim les dades de la URL: " + sURL)
bDadesZIP = requests.get(sURL)
if bDadesZIP.status_code != requests.codes.ok:
	print ("Error " + bDadesZIP.status_code + " en la descàrrega del fitxer " + sURL)
	exit ()
print("S'ha obtingut el fitxer de data " + bDadesZIP.headers["Last-Modified"])

# Extracció del contingut ZIP 
file_like_object = io.BytesIO(bDadesZIP.content)
zipfile_ob = zipfile.ZipFile(file_like_object)
zipfile_ob.extractall()

# Obtenció de les dades del fitxer CSV.
fDades = open(zipfile_ob.namelist()[0], "rt")
sIndex = fDades.readline().split(";")
"""
NOM;CODI;DATA_INI;DATA_FI;IEPG_CONFIRMAT;R0_CONFIRMAT_M;IA14;TAXA_CASOS_CONFIRMAT;CASOS_CONFIRMAT;TAXA_PCRTAR;PCR;TAR;PERC_PCRTAR_POSITIVES;INGRESSOS_TOTAL;INGRESSOS_CRITIC;EXITUS;CASOS_PCR;CASOS_TAR;POSITIVITAT_PCR_NUM;POSITIVITAT_TAR_NUM;POSITIVITAT_PCR_DEN;POSITIVITAT_TAR_DEN;VACUNATS_DOSI_1;VACUNATS_DOSI_2
"""

if "IA14" in sIndex:
	iIndexColIA14 = sIndex.index("IA14")
else:
	print ("Error en el format de les dades: No s'ha trobat el camp IA14")
	exit()
	
if "DATA_FI" in sIndex:
	iIndexColDataFi = sIndex.index("DATA_FI")
else:
	print ("Error en el format de les dades: No s'ha trobat el camp DATA_FI")
	exit()

for x in fDades:
	sData = x.split(";")[iIndexColDataFi]
	dData = datetime.datetime.strptime(sData,"%Y-%m-%d").date()
	aDates.append(dData)
	aIA14.append(float(x.split(";")[iIndexColIA14]))

fDades.close()

# Tractament de les dades obtingudes
aDates.reverse()
aIA14.reverse()
aDatesNum = mdates.date2num(aDates)

# Obtenció de la velocitat d'evolució IA14 (increment diari)
aVelIA14.append(aIA14[0])
iXAnt = aIA14[0]
for x in aIA14[1:]:
	aVelIA14.append(x-iXAnt)
	iXAnt = x

# Obtenció del promig de la velocitat d'evolució IA14 (increment diari)
iLimCalculProm = 10
aPromVelIA14[:iLimCalculProm] = aVelIA14[:iLimCalculProm]

for iIndex in range (iLimCalculProm, len(aVelIA14)):
	iCalculProm = 0
	for i in range (0, iLimCalculProm):
		iCalculProm += (aVelIA14[iIndex - i])
	aPromVelIA14.append(iCalculProm/iLimCalculProm)

# Obtenció de l'acceleració d'evolució IA14 (increment diari)
aAccelIA14.append(aVelIA14[0])
iXAnt = aVelIA14[0]
for x in aVelIA14[1:]:
	aAccelIA14.append(x-iXAnt)
	iXAnt = x

# Creació dels segments de la grafica de velocitat:
# - Creem un array de punts a partir de les dates en fomrat numèric (Eix X) i el valor de la velocitat (Eix Y)
# - Creem un array de segments concatenant els punts obtinguts inicialment
# - Creem la llista de colors a partir de l'acceleració en el punt

aPunts = np.array([aDatesNum, aVelIA14]).T.reshape(-1,1,2)
aSegments = np.concatenate([aPunts[:-1], aPunts[1:]], axis=1)
aColors = [(1, 0, 0) if x >= 0 else (0, 1, 0) for x in aAccelIA14[1:]]
lcSegments = LineCollection(aSegments, colors=aColors, label="Velocitat IA14")

# Visualització dels resultats

fig = plt.figure()
ax1 = fig.add_subplot(111)

# Viaulització de la variable aIA14 corresponent a l'evolució de l'indicador IA14
ax1.plot(aDatesNum, aIA14, color=lLlegenda [0][0], label=lLlegenda [0][1])
ax1.set_ylabel("Evolució IA14", fontsize=14)
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m/%Y"))
ax1.xaxis.set_major_locator(mdates.MonthLocator())

# Viaulització, en un eix diferent, de la velocitat d'evolució de l'indicador IA14
ax2=ax1.twinx()
ax2.add_collection(lcSegments)
ax2.set_ylim(min(aVelIA14)*1.1, max(aVelIA14)*1.1)
ax2.set_ylabel("Velocitat IA14", fontsize=14)

# Viaulització, al segon eix, del promig de la velocitat d'evolució de l'indicador IA14
ax2.plot(aDatesNum, aPromVelIA14, color=lLlegenda [3][0])

# Alineació dels eixos Y
align_yaxis_np(ax1, ax2)

# Llegenda de la gràfica
lColorsLlegenda = []
lTtitolsLlegenda = []
for x in lLlegenda:
	lColorsLlegenda.append(Line2D([0], [0], color=x[0], lw=2))
	lTtitolsLlegenda.append(x[1])

ax1.legend(lColorsLlegenda,
	lTtitolsLlegenda)

# Afegim línies horitzontals indicant els diferents valors de referència de l'indicador IA14
plt.hlines(y=0, xmin=min(aDatesNum)-10, xmax=max(aDatesNum)+10, color="gray", linestyles="dashed")
for x in lLinRefIA14:
	ax1.hlines(y=x[0], xmin=min(aDatesNum)-10, xmax=max(aDatesNum)+10, color=x[1], label=x[2])
	ax1.text(mdates.date2num(aDates[0])-20, x[0], x[2])

# Rotacio dels títols de l'eix X
ax1.tick_params(axis="x", labelrotation=45)

# Títol del gràfic
sTitol = "Evolució de l'indicador IA14 \n"
sTitol += aDates[0].strftime("%d/%m/%Y") + " - " + aDates[-1].strftime("%d/%m/%Y" + "\n")
plt.title(sTitol)
plt.show()

