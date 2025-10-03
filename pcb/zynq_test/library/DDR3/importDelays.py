from kipy import KiCad
import pandas as pd


outerLayer_ps_cm = 60.29696
traceDelay = outerLayer_ps_cm/10
print(traceDelay)
df = pd.read_csv("pin_delay.csv")


kicad = KiCad()
board = kicad.get_board()
footprints = board.get_footprints()
footprints = [f for f in footprints if f.value_field.text.value == "MT41K256M16TW-107"]
a = 0
for f in footprints:
    print(f.reference_field)
    for i,p in enumerate(f.definition.pads):
        pin = df[df['Pin']==p.number]
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