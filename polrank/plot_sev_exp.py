import os
import sys
import numpy as np
from utils.logging import Logger
from visualisation.graphing import draw_interpol_results

if __name__ == '__main__':
    if len(sys.argv) == 2:
        pref = sys.argv[1]
    else:
        print("Usage: python polexp/plot_sev_exps PREFIX")
        print("Where PREFIX is the prefix is the name of the results directories, e.g. Breakout for Breakout_0, Breakout_1 ...")
        print("This will plot the results from all the directories with this prefix averaged, and save them in the first directory.")
        exit()

    fls = [fl for fl in os.listdir('results') if fl.startswith('{}_'.format(pref))]
    # Get all the loggers
    loggers = [Logger(fl) for fl in fls]
    for logger in loggers:
        logger.load_results()

    draw_interpol_results(loggers, ["zoltar", "tarantula", "wongII", "ochiai", "rand", "freqVis"], 0, [1], x_fracs=True, y_fracs=True, smooth=False,
        x_name='States Restored (%)', y_names=['Original Reward (%)'], combine_sbfl=False)
    draw_interpol_results(loggers, ["zoltar", "tarantula", "wongII", "ochiai", "rand", "freqVis"], 4, [1], y_fracs=True,
        trans_x=lambda x: 1-x, x_name="Policy's Action Taken (% of Steps)",
        y_names=['Original Reward (%)'], smooth=False, combine_sbfl=False)
