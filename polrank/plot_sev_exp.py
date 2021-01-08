import os
import numpy as np
from utils.logging import Logger
from visualisation.graphing import draw_interpol_results

FL_PREFIXS = ['Alien', 'Atlantis', 'Boxing', 'Breakout', 'DemonAttack', 'IceHockey', 'Pong', 'Qbert', 'SpaceInvaders']

if __name__ == '__main__':
    for pref in FL_PREFIXS:
        fls = [fl for fl in os.listdir('results') if fl.startswith('uber{}_'.format(pref))]
        # Get all the loggers
        loggers = [Logger(fl) for fl in fls]
        for logger in loggers:
            logger.load_results()

        draw_interpol_results(loggers, ["zoltar", "tarantula", "wongII", "ochiai", "rand", "freqVis"], 0, [1], x_fracs=True, y_fracs=True, smooth=False,
            x_name='States Restored (%)', y_names=['Original Reward (%)'], combine_sbfl=False)
        draw_interpol_results(loggers, ["zoltar", "tarantula", "wongII", "ochiai", "rand", "freqVis"], 4, [1], y_fracs=True,
            trans_x=lambda x: 1-x, x_name="Policy's Action Taken (% of Steps)",
            y_names=['Original Reward (%)'], smooth=False, combine_sbfl=False)
