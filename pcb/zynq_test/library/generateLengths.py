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


dram = [t for t in tracks if "/Zynq Dram/" in t.net.name]
layers = set([l.layer for l in dram])
nets = set([n.net.name.replace("/Zynq Dram/","") for n in dram])
nets = dict.fromkeys(nets)
nets = {k:dict.fromkeys(layers,0.0) for k in nets.keys()}
for t in dram:
    nets[t.net.name.replace("/Zynq Dram/","")][t.layer] += t.length()

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

footprints = [f for f in board.get_footprints() if f.reference_field.text.value in ["U402"]]

df["U402_ps"] = [0.0]*len(df)
for p in footprints[0].definition.pads: 
    if p.pad_to_die_length > 0:
        df.loc[df['Net'] == p.net.name.replace("/Zynq Dram/",""),'U402_ps'] = float(p.pad_to_die_length)/1000000*outerLayer_ps_mm

# Zynq was calculated with slightly diferrent delay
traceDelay_Zynq = 151.31928 #(ps/in)
traceDelay_Zynq = traceDelay_Zynq * 0.03937008 #(ps/mm)
print(traceDelay_Zynq)

footprints = [f for f in board.get_footprints() if f.reference_field.text.value in ["U202"]]
df["Zynq_ps"] = [0.0]*len(df)
for p in footprints[0].definition.pads:
    if len(df[df['Net'] == p.net.name.replace("/Zynq Dram/","")]) > 0:
        if p.pad_to_die_length > 0:
            df.loc[df['Net'] == p.net.name.replace("/Zynq Dram/",""),'Zynq_ps'] = float(p.pad_to_die_length)/1000000*traceDelay_Zynq

vias = board.get_vias()
df["Via Count"] = [0]*len(df)
for v in vias: 
    if len(df[df['Net'] == v.net.name.replace("/Zynq Dram/","")]) > 0:
        df.loc[df['Net'] == v.net.name.replace("/Zynq Dram/",""),'Via Count'] += 1

df["Via_ps"] = [0]*len(df)
for i,r in df.iterrows():
    length = 0.0
    if r['In3.Cu'] > 1.0:
        length = 0.3157
    elif r['In5.Cu'] > 1.0:
        length = 0.5299
    elif r['B.Cu'] > 1.0:
        length = 0.7216
    df.loc[i,"Via_ps"] =  r["Via Count"]*length*via_ps_mm


df["total_routed_length_mm"] = np.sum(df[[l for l in layersNames]],axis=1)
df["total_ps"] = np.sum(df[[l+"_ps" for l in layersNames]+['Via_ps',"Zynq_ps","U402_ps"]],axis=1)
df["Goal_ps"] = [0.0]*len(df)
df["Top_add_mm"] = [0.0]*len(df)
df["Top_total_mm"] = [0.0]*len(df)
df["inner_add_mm"] = [0.0]*len(df)
df["inner_total_mm"] = [0.0]*len(df)

address_control_bool = ~df['Net'].str.contains("DDR_L") & ~df['Net'].str.contains("DDR_CTR.RST")
address_control = df[address_control_bool]
df.loc[address_control.index,'Goal_ps'] = address_control['total_ps']-max(address_control['total_ps'])+ps_tolerance

for i in range(4):
    ddr_l = df[df['Net'].str.contains("DDR_L"+str(i))]
    if len(ddr_l) > 0:
        df.loc[ddr_l.index,'Goal_ps'] = ddr_l['total_ps']-max(ddr_l['total_ps'])+ps_tolerance

df["Top_add_mm"] = df['Goal_ps']/outerLayer_ps_mm*-1
df["Top_total_mm"] = df['total_routed_length_mm']+df["Top_add_mm"]

df["inner_add_mm"] = df['Goal_ps']/inneLayer_ps_mm*-1
df["inner_total_mm"] = df['total_routed_length_mm']+df["inner_add_mm"]

addr_only = df['Net'].str.contains("DDR_L2")
print(df.sort_values(by='Net')[["Net","total_ps","Goal_ps","Top_add_mm","Top_total_mm",
                                "inner_add_mm","inner_total_mm"]])
# df.sort_values(by='Net').to_csv("ddrU402.csv")
