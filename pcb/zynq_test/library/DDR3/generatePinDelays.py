import pandas as pd
import numpy as np
lines = open("importedIbis.txt").readlines()
startingLine = [i for i,x in enumerate(lines) if "[Pin]" in x]
lines = lines[startingLine[0]:]
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
    except ValueError:
        return inp
    return inp
lines = [[y if i <3 else convertDelay(y) for i,y in enumerate(x)] for x in lines]
lines = [x if len(x) == 6 else (x+[float('nan')]*(6-len(x))) for x in lines]

df = pd.DataFrame(lines[1:],columns=lines[0])
df['Max Trace Delay (ps)'] = np.sqrt(df['L_pi']*df['C_pi'])*1.0000E+12

print(max(df['Max Trace Delay (ps)'].fillna(0)), min(df['Max Trace Delay (ps)'].fillna(1000)))
df['Max Trace Delay (ps)'] = df['Max Trace Delay (ps)'].fillna('')
df.to_csv('pin_delay.csv')
