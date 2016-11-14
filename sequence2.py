### Caution: Python is sensitive for indentation. Do use "Space" insted of "Tab".

dV = 50 # (V) Minimum volgage step, which must be a dvisor for holding voltages.


# List of [Voltage (V), holding time(s)]
DT = 1200 # (s) time per step for time-dependence measurement
#SEQ = [[5000, 360000]]
SEQ = [#[2000, DT],\
        #[2100, DT],\
        [3000, DT],\
        [3100, DT],\
        [3200, DT],\
        [3300, DT],\
        [3400, DT],\
        [3500, DT],\
        [3600, DT],\
        [3700, DT],\
        [3800, DT],\
        [3900, DT],\
        [4000, 900+DT],\
        [4050, 900+DT],\
        [4100, 900+DT],\
        [4150, 900+DT],\
        [4200, 900+DT],\
        [4250, 900+DT],\
        [4300, 900+DT],\
        [4350, 900+DT],\
        [4400, 900+DT],\
        [4450, 900+DT],\
        [4500, 2*DT],\
        [4550, 2*DT],\
        [4600, 2*DT],\
        [4650, 2*DT],\
        [4700, 2*DT],\
        [4750, 2*DT],\
        [4800, 2*DT],\
        [4850, 2*DT],\
        [4900, 2*DT],\
        [4950, 2*DT],\
        [5000, 360000]]
