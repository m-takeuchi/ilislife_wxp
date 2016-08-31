### Caution: Python is sensitive for indentation. Do use "Space" insted of "Tab".

dV = 50 # (V) Minimum volgage step, which must be a dvisor for holding voltages.


# List of [Voltage (V), holding time(s)]
DT = 60 # (s) time per step for time-dependence measurement
#SEQ = [[5000, 360000]]
SEQ = [[1000, DT],\
        [2000, DT],\
        [3000, DT]]
