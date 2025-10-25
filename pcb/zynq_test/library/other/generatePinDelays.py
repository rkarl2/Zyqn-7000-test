import pandas as pd
import numpy as np

lines = open("lanibis.txt").readlines()
startingLine = [i for i,x in enumerate(lines) if "[Pin]" in x]
lines = lines[startingLine[0]:]
lines = [x.replace('\t',' ') for x in lines]
lines = [[y for y in x.strip("\n").split(' ') if len(y) > 0] for x in lines]
lines[0][0] = "Pin"
lines = [[y if i <4 else y.replace('H','').replace('F','') for i,y in enumerate(x)] for x in lines]
def convertDelay(inp:str):
    try:
        if 'm' in inp:
            inp = inp.replace('m','')
            inp = float(inp)/1000
        elif 'n' in inp:
            inp = inp.replace('n','')
            inp = float(inp)/1.0000E+9
        elif 'p' in inp:
            inp = inp.replace('p','')
            inp = float(inp)/1.0000E+12
        else:
            float(inp)
    except ValueError:
        if inp == "NA":
            return 0.0
    return inp
lines = [[y if i <3 else convertDelay(y) for i,y in enumerate(x)] for x in lines]
lines = [x if len(x) == 6 else (x+[float('nan')]*(6-len(x))) for x in lines]

df = pd.DataFrame(lines[1:],columns=lines[0])
print(df)
df['Max Trace Delay (ps)'] = np.sqrt(df['L_pi'].astype(np.float32)*df['C_pi'].astype(np.float32))*1.0000E+12

print(max(df['Max Trace Delay (ps)'].fillna(0)), min(df['Max Trace Delay (ps)'].fillna(1000)))
df['Max Trace Delay (ps)'] = df['Max Trace Delay (ps)'].fillna('')
df.to_csv('pin_delay_LAN.csv')
