from kipy import KiCad
from kipy import util
import pandas as pd
import numpy as np

# tolerance is +- 10 ps, total delta 20ps
# Choose to half it +- 5, 10
ps_tolerance = 10

inneLayer_ps_cm = 67.30725
inneLayer_ps_mm = inneLayer_ps_cm/10
outerLayer_ps_cm = 60.29696
outerLayer_ps_mm = outerLayer_ps_cm/10

# Calculated based on SQRT(E) / c 
# E = 3.3
via_ps_mm = 6

kicad = KiCad()
board = kicad.get_board()
tracks = board.get_tracks()


dram = [t for t in tracks if "/ETHERNET/" in t.net.name]
layers = set([l.layer for l in dram])
nets = set([n.net.name.replace("/ETHERNET/","") for n in dram])
nets = dict.fromkeys(nets)
nets = {k:dict.fromkeys(layers,0.0) for k in nets.keys()}
for t in dram:
    nets[t.net.name.replace("/ETHERNET/","")][t.layer] += t.length()

layers = {k:util.board_layer.canonical_name(k) for k in layers}
netLengths = dict.fromkeys(["Net"]+[v for v in layers.values()])
netLengths = {k:[] for k in netLengths}
for netName,LayerVal in nets.items():
    netLengths['Net'].append(netName)
    
    for layer,length in LayerVal.items():
        netLengths[layers[layer]].append(length)

layersNames = [l for l in layers.values()]
print(layersNames)
df = pd.DataFrame(netLengths)

# Convert pm to mm
for l in layersNames:  df[l] = df[l].apply(lambda x: x/1_000_000)
for l in layersNames:  df[l+"_ps"] = df[l]*inneLayer_ps_mm if "In" in l else df[l]*outerLayer_ps_mm

footprints = [f for f in board.get_footprints() if f.reference_field.text.value in ["U401"]]

# Zynq was calculated with slightly diferrent delay
traceDelay_Zynq = 151.31928 #(ps/in)
traceDelay_Zynq = traceDelay_Zynq * 0.03937008 #(ps/mm)


vias = board.get_vias()
df["Via Count"] = [0]*len(df)
for v in vias: 
    if len(df[df['Net'] == v.net.name.replace("/ETHERNET/","")]) > 0:
        df.loc[df['Net'] == v.net.name.replace("/ETHERNET/",""),'Via Count'] += 1

df["Via_ps"] = [0]*len(df)
for i,r in df.iterrows():
    length = 0.0
    if r['In3.Cu'] > 1.0:
        length = 0.3157
    elif r['In5.Cu'] > 1.0:
        length = 0.5299
    if r['B.Cu'] > 1.0:
        length = 0.7216
    df.loc[i,"Via_ps"] =  r["Via Count"]*length*via_ps_mm


df["total_routed_length_mm"] = np.sum(df[[l for l in layersNames]],axis=1)
df["total_ps"] = np.sum(df[[l+"_ps" for l in layersNames]+['Via_ps']],axis=1)
df["Goal_ps"] = [0.0]*len(df)
df["Top_add_mm"] = [0.0]*len(df)
df["Top_total_mm"] = [0.0]*len(df)
df["inner_add_mm"] = [0.0]*len(df)
df["inner_total_mm"] = [0.0]*len(df)


# for i in range(4):
#     ddr_l = df[df['Net'].str.contains("DDR_L"+str(i))]
#     if len(ddr_l) > 0:
#         df.loc[ddr_l.index,'Goal_ps'] = ddr_l['total_ps']-max(ddr_l['total_ps'])+ps_tolerance

df["Top_add_mm"] = df['Goal_ps']/outerLayer_ps_mm*-1
df["Top_total_mm"] = df['total_routed_length_mm']+df["Top_add_mm"]

df["inner_add_mm"] = df['Goal_ps']/inneLayer_ps_mm*-1
df["inner_total_mm"] = df['total_routed_length_mm']+df["inner_add_mm"]

addr_only = df['Net'].str.contains("TX")
rx_only = df['Net'].str.contains("TX")
RX = df[rx_only]
# before = RX[RX['Net'].str.endswith(".L")]
# after = RX[~RX['Net'].str.endswith(".L")]
# np.array(before.sort_values(by='Net')['total_ps'])+np.array(after.sort_values(by='Net')['total_ps'])

# x = list(zip(np.array(before.sort_values(by='Net')['total_ps'])+np.array(after.sort_values(by='Net')['total_ps']),before.sort_values(by='Net')['Net']))
# for a in x: print(a)
# print(df[addr_only].sort_values(by='Net')[[l for l in layersNames]+['Net']])
print(df[addr_only].sort_values(by='Net')[['Net','total_ps','total_routed_length_mm','Top_add_mm']])
# df.sort_values(by='Net').to_csv("ddrU401.csv")
