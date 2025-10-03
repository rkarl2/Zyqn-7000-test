from kipy import KiCad
import pandas as pd


traceDelay = 151.31928 #(ps/in)
traceDelay = traceDelay * 0.03937008 #(ps/mm)
print(traceDelay)
df = pd.read_csv("pin_delay.csv",skiprows=[0,1,2,3,4,5])


kicad = KiCad()
board = kicad.get_board()
footprints = board.get_footprints()
footprints = [f for f in footprints if f.value_field.text.value == "XC7Z020-2CLG400I"]
a = 0
for f in footprints:
    for i,p in enumerate(f.definition.pads):
        
        pin = df[df['Pin Number']==p.number]
        if(len(pin) ==1):
            if not all(pin["Max Trace Delay (ps)"].isna()):
                # print(pin)
                delay= float(pin["Max Trace Delay (ps)"])
                delay = delay/traceDelay
                p.pad_to_die_length = int(delay*1000000)
                
                print(f.definition.pads[i].pad_to_die_length)
                a = a+1
    board.update_items(f)
    # print(f.definition.pads[0].number)
print(a)
# print(df['Pin Number'])