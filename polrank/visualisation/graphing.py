import os

import numpy as np
import matplotlib.pyplot as plt

from scoring import ST_COLOURS

def draw_interpol_results(loggers, score_types, which_x, which_ys,
    trans_x=lambda x: x, x_name=None, y_names=None,
    hlines=False, x_fracs=False, y_fracs=False, y_offset=0, saveloc=None,
    smooth=False, combine_sbfl=False):
    ''' Given score types, which x axis to use, and several y axes: makes as many graphs as
    y axes. Plots results for all score_types on one graph.

    trans_x: is function applied to all x-axis values
    x_name: replaces x-axis name if provided
    hlines: is created from data at end of y lists
    y_fracs: makes y-axis fraction of baseline values (end of y lists) 
    
    
    CURRENTLY X_FRACS DOES NOTHING - ALWAYS TAKES FRACS IN mean_and_var '''

    if not isinstance(loggers, list):
        loggers = [loggers]

    # For all three of these, there is one item for each logger
    all_xs = []
    all_yss = []
    all_hvals = []
    for logger in loggers:
        data = logger.data['interpol'][0]
        # One for each score_type
        xs = [list(map(trans_x, data[st][which_x]))[:-1] for st in score_types]
        # One for each y-axis, and then for each score_type
        yss = [[data[st][wy] for st in score_types] for wy in which_ys]

        # if x_fracs:
        #     xs = [[val/max(x) for val in x] for x in xs]
        if y_offset:
            new_yss = []
            for ys in yss:
                new_yss.append([[val-y_offset for val in vals] for vals in ys])
            yss = new_yss

        # Get final values for baseline and remove them
        hvals = [np.mean([vals[-1] for vals in ys]) for ys in yss]
        yss = [[vals[:-1] for vals in ys] for ys in yss]

        all_xs.append(xs)
        all_hvals.append(hvals)
        all_yss.append(yss)

    # Currently all_hvals has an entry for each logger, which 
    # is a list of the hvals for each y axis.
    # Averages across loggers
    hvals = [np.mean([hvals[log_ind] for hvals in all_hvals]) for log_ind in range(len(all_hvals[0]))]

    if y_fracs:
        for log_ind, yss in enumerate(all_yss):
            new_yss = []
            for ys, hval in zip(yss, hvals):
                new_yss.append([[(val/hval) for val in vals] for vals in ys])
            all_yss[log_ind] = new_yss
        hvals = [1] * len(which_ys)

    if not hlines:
        hvals = [None] * len(which_ys)

    x_name = x_name if x_name is not None else loggers[0].interpol_cols[which_x]
    y_names = y_names if y_names is not None else[loggers[0].interpol_cols[wy] for wy in which_ys]

    saveloc = saveloc if saveloc is not None else loggers[0].fileloc
    savelocs = [os.path.join(saveloc, x_name + '_' + y_name + '_' + '_'.join(score_types)) for y_name in y_names]

    # For each y-axis (i.e. new graph) get all the relevant data from the loggers
    yss_per_graph = [[yss[which_y] for yss in all_yss] for which_y in range(len(which_ys))]

    for all_ys, y_name, hv, sl in zip(yss_per_graph, y_names, hvals, savelocs):
        # all_xs and all_ys is one for each logger and then one for each score_type
        draw_curves(all_xs, all_ys, x_name, y_name, score_types, hval=hv, sloc=sl, smooth=smooth, combine_sbfl=combine_sbfl)

def smoothing(x, y, spline=False):
    # Make sure x and y are sorted properly first!

    if spline: # Currently fails if 2 x-values are the same
        from scipy import interpolate
        smoothness = 0 # Amount of smoothness - 0 is usually enough
        x_smooth = np.linspace(x.min(), x.max(), 300)
        tck = interpolate.splrep(x, y, s=smoothness)
        y_smooth = interpolate.splev(x_smooth, tck, der=0)
        return x_smooth, y_smooth

    window = 3 # Must be odd
    new_y = []
    for i in range(len(y)):
        w = min(int(window/2), i, len(y)-i-1) # How far can the window extend to the right or left
        new_y.append(sum(y[i-w:i+w+1])/((2*w)+1))

    return x, new_y

def draw_curves(all_xs, all_ys, x_name, y_name, score_types, hval=None, sloc=None, smooth=False, combine_sbfl=False):
    plt.clf()

    ## Pretty hacky, combines SBFL lines while only taking point which improve on the previous
    if combine_sbfl:
        new_all_xs = []
        new_all_ys = []
        for xs, ys in zip(all_xs, all_ys):
            new_xs, new_ys, new_st, sbfl_x, sbfl_y = [], [], [], [], []
            for x, y, st in zip(xs, ys, score_types):    
                if st in ["zoltar", "tarantula", "wongII", "ochiai"]:
                    sbfl_x.append(x)
                    sbfl_y.append(y)
                else:
                    new_xs.append(x)
                    new_ys.append(y)
                    new_st.append(st)

            sbfl_x, sbfl_y = combine_lines(sbfl_x, sbfl_y, only_improve=True)
            new_xs.append(sbfl_x)
            new_ys.append(sbfl_y)
            new_st.append('SBFL')

            new_all_xs.append(new_xs)
            new_all_ys.append(new_ys)
        score_types = new_st
        all_xs = new_all_xs
        all_ys = new_all_ys
    ##

    xs, mean_ys, std_ys = mean_and_var(all_xs, all_ys)

    xmax = 0
    for x, m_y, std_y, st in zip(xs, mean_ys, std_ys, score_types):
        xmax = max(xmax, max(x))

        print(st)
        for xv, yv in zip(x, m_y):
            if yv >= .9:
                print(xv)
                break
        for xv, yv in zip(x, m_y):
            if yv >= .5:
                print(xv)
                break

        if smooth:
            x, y = smoothing(x, y)

        ## Very hacky, turn into percentages
        if '%' in y_name:
            m_y = [val*100 for val in m_y]
            std_y = [val*100 for val in std_y]
        if '%' in x_name:
            x = [val*100 for val in x]
        ##

        ## Hacky, makes sure non-SBFL lines also only taking point that improve
        if st in ['rand', 'freqVis', 'tarantula', 'ochiai', 'zoltar', 'wongII']:
            x, m_y, std_y = only_improve(x, m_y, std_y)
        ##

        if st == 'rand':
            plt.plot(x, m_y, linestyle='dashed', label=st, color=ST_COLOURS[st], linewidth=3)
        else:
            plt.plot(x, m_y, label=st, color=ST_COLOURS[st], linewidth=3)

        m_y, std_y = np.array(m_y), np.array(std_y)
        plt.fill_between(x, m_y-std_y, m_y+std_y, color=ST_COLOURS[st], alpha=0.2)

    if hval is not None:
        # plt.plot([0, xmax], [hval, hval], linestyle='dashed', label='baseline')
        plt.axhline(y=hval, xmin=0, xmax=1, linestyle='dotted', label='baseline', color='red')

    # axes = plt.axes()
    # axes.set_ylim([0, 110])

    plt.legend()
    plt.ylabel(y_name, size=17)
    plt.xlabel(x_name, size=17)
    plt.tight_layout()

    if sloc is not None:
        plt.draw()
        plt.savefig(sloc+'.eps', format='eps')
        plt.savefig(sloc+'.png', format='png')
    else:
        plt.show()

    plt.clf()

def move_counter(start_ind, target_x, xys):
    # Starting from start_ind, find index of ts right before it goes above target_t
    try:
        ind = start_ind
        while xys[ind+1][0] < target_x:
            ind += 1
        return ind
    except IndexError:
        return ind

def interpolate(first_ind, target_x, xys):
    # Find the value of ts at target_t by interpolating between values at
    # first_ind and first_ind+1
    if first_ind == len(xys) - 1 or (xys[first_ind+1][0] - xys[first_ind][0]) == 0:
        return xys[first_ind][1]
    else:
        base = xys[first_ind][1]
        change = xys[first_ind+1][1] - base
        time_diff = xys[first_ind+1][0] - xys[first_ind][0]
        slope = change / time_diff
        return base + (slope * (target_x - xys[first_ind][0]))

def mean_and_var(all_xs, all_ys):
    st_xs = []
    st_mean_ys = []
    st_std_ys = []
    # For each score type, get a line, using xs from first logger
    for st in range(len(all_xs[0])):
        score_type_data = [(xss[st], yss[st]) for xss, yss in zip(all_xs, all_ys)]
        score_type_data = [list(zip(xs, ys)) for xs, ys in score_type_data]
        for data in score_type_data:
            data.sort(key=lambda xy: xy[0])

        counters = [0] * (len(score_type_data) - 1)
        final_xs = []
        final_ys = []
        final_std = []
        for x, y in score_type_data[0]:
            ys = [y] # all the y values at this x value
            for i in range(len(score_type_data)-1):
                counters[i] = move_counter(counters[i], x, score_type_data[i+1])
                ys.append(interpolate(counters[i], x, score_type_data[i+1]))
            final_xs.append(x)
            final_ys.append(np.mean(ys))
            final_std.append(np.std(ys))
        
        x_max = max(final_xs)
        x_fracs = [x / x_max for x in final_xs]
        st_xs.append(x_fracs)
        st_mean_ys.append(final_ys)
        st_std_ys.append(final_std)

    return st_xs, st_mean_ys, st_std_ys

    # data = [{} for _ in range(len(all_xs[0]))] # score_type x x_val x y_vals
    # # all_xs: num_loggers x score_types x data
    # for xss, yss in zip(all_xs, all_ys): # Data from each logger
    #     for score_type_ind, (xs, ys) in enumerate(zip(xss, yss)): # Each score type
    #         for x, y in zip(xs, ys): # Each point
    #             if x in data[score_type_ind]:
    #                 data[score_type_ind][x].append(y)
    #             else:
    #                 data[score_type_ind][x] = [y]

    # st_xs = []
    # st_mean_ys = []
    # st_std_ys = []
    # for st_data in data:
    #     import pdb; pdb.set_trace()
    #     st_data = [(x, ys) for x, ys in st_data.items() if len(ys) == n_loggers]
    #     st_data.sort(key=lambda i: i[0])
    #     mean_ys = [np.mean(ys) for x, ys in st_data]
    #     std_ys = [np.std(ys) for x, ys in st_data]
    #     xs = [x for x, ys in st_data]
    #     xmax = max(xs)
    #     import pdb; pdb.set_trace()
    #     frac_xs = [x/xmax for x in xs]
    #     st_xs.append(frac_xs)
    #     st_mean_ys.append(mean_ys)
    #     st_std_ys.append(std_ys)
    
    # return st_xs, st_mean_ys, st_std_ys

def combine_lines(xs, ys, only_improve=False):
    """ Take list of lists for xs and ys (for each score type)
    and use best in each point. """

    all_points = [(x_val, y_val) for x, y in zip(xs, ys) for x_val, y_val in zip(x, y)]
    all_points.sort(key=lambda tup: tup[0])

    xmax = all_points[-1][0]

    combined_x = [all_points[0][0]]
    combined_y = [all_points[0][1]]

    if only_improve:
        for x_val, y_val in all_points[1:]:
            if x_val == combined_x[-1]:
                combined_y[-1] = max(y_val, combined_y[-1])
            elif y_val > combined_y[-1]:
                combined_x.append(x_val)
                combined_y.append(y_val)
        combined_x.append(xmax)
        combined_y.append(combined_y[-1])
    else:
        for x_val, y_val in all_points[1:]:
            if x_val == combined_x[-1]:
                combined_y[-1] = max(y_val, combined_y[-1])
            else:
                combined_x.append(x_val)
                combined_y.append(y_val)

    return combined_x, combined_y

def only_improve(xs, m_ys, std_ys):
    """ Takes list of x values and list of y values """
    new_xs, new_ys, new_std_ys = [xs[0]], [m_ys[0]], [std_ys[0]]
    for x, y, std_y in zip(xs[1:], m_ys[1:], std_ys[1:]):
        if x == new_xs[-1]:
            new_ys[-1] = max(new_ys[-1], y)
            new_std_ys[-1] = std_y
        elif y > new_ys[-1]:
            new_xs.append(x)
            new_ys.append(y)
            new_std_ys.append(std_y)
    if new_xs[-1] < xs[-1]:
        new_xs.append(xs[-1])
        new_ys.append(new_ys[-1])
        new_std_ys.append(std_ys[-1])

    return new_xs, new_ys, new_std_ys

def cartpole_graphs(fileloc, scores, score_types):
    import matplotlib.pyplot as plt 
    import numpy as np
    from scoring import ST_COLOURS

    x_names = ['CartPos', 'CartSpeed', 'PoleAng', 'PoleSpeed']
    for i in range(4):
        plt.clf()
        for st in score_types:
            scrs = scores[st]
            vals = {}
            for s, sc in scrs:
                s = s[1:-1].split(',')
                x = float(s[i])
                if x in vals:
                    vals[x].append(sc)
                else:
                    vals[x] = [sc]

            for s, sc in vals.items():
                vals[s] = np.mean(sc)

            vals = list(vals.items())
            vals.sort(key=lambda tup:tup[0])
            vals = list(zip(*vals))

            diff = max(vals[1])-min(vals[1])
            if diff > 0:
                vals[1] = [(i-min(vals[1]))/diff for i in vals[1]]
            else:
                vals[1] = [0 for i in vals[1]]
            plt.plot(vals[0], vals[1], label=st, color=ST_COLOURS[st], linewidth=3)

        plt.legend()
        plt.ylabel('Score', size=17)
        plt.xlabel(x_names[i], size=17)
        plt.tight_layout()
        plt.draw()
        plt.savefig(fileloc + str(i) + '.png')

        # plt.clf()
        # for st in score_types:
        #     scrs = scores[st]
        #     xs, ys = [], []
        #     for s, sc in scrs:
        #         s = s[1:-1].split(',')
        #         x = float(s[i])
        #         xs.append(x)
        #         ys.append(sc)

        #     diff = max(ys)-min(ys)
        #     if diff > 0:
        #         ys = [(i-min(ys))/diff for i in ys]
        #     else:
        #         ys = [0 for i in ys]
        #     plt.scatter(xs, ys, s=2, label=st, color=ST_COLOURS[st])

        # plt.legend()
        # plt.ylabel('Score', size=17)
        # plt.xlabel(x_names[i], size=17)
        # plt.tight_layout()
        # plt.draw()
        # plt.savefig(fileloc + str(i) + '_scatter.png')