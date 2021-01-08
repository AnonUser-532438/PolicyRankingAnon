import random

import numpy as np
import torch

from counting import count
from scoring import score
from interpolating import interpolate
import utils.cli as cli
from utils.logging import Logger
from visualisation.graphing import draw_interpol_results
from visualisation.histograms import score_histogram
from visualisation.see_env import run_and_save

def main():
    args = cli.parse_args()

    if not args.no_det:
        np.random.seed(args.env_seed)
        random.seed(args.env_seed)
        torch.manual_seed(args.env_seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    ### Logger setup ###
    logger = Logger(args.fileloc, args.load_loc)
    logger.init_config(args)
    logger.load_results()

    ### If we're making a visualisation, branch here ###
    if args.task == 'vis':
        if False:
            import imageio
            import os
            env = logger.config['env']
            state = env.reset()
            for _ in range(20):
                state, _, _, _ = env.step(0)
            env.vis_type = -1
            rgb = env.get_RGB(env, state, None, None)
            raw_abst = env.abst(rgb)
            import pdb; pdb.set_trace()
            env.vis_type = 0
            abst = env.get_RGB(env, state, None, None)
            imageio.imsave(os.path.join(logger.fileloc, 'pong_rgb.png'), rgb)
            imageio.imsave(os.path.join(logger.fileloc, 'pong_abs.png'), abst)
            exit()
        if args.ranking not in logger.data['scores'][0]:
            print("\nNeed to compute ranking {} before doing visualisation!".format(args.ranking))
            exit()
        run_and_save(logger)
        exit()

    ### Get or update all results ###
    counts_do = {
        'redo': args.redo_all or not logger.is_done('counts'),
        'update': args.more_count is not None
    }
    scores_do = {
        'redo': counts_do['redo'] or counts_do['update'] or not logger.is_done('scores'),
        'update': args.more_scoretypes is not None
    }
    interpol_do = {
        'redo': scores_do['redo'] or not logger.is_done('interpol') or args.redo_interpol is not None,
        'update': scores_do['update']
    }

    ### Counts
    if counts_do['redo']:
        print("\n----- Counting -----\n")
        counts = count(logger)
        logger.update_counts(counts)

    if counts_do['update']:
        N = args.more_count
        print("\n----- Additional Counts ({} more runs) -----\n".format(N))

        # If we're adding more counts without having run before, then we need to reset the
        # env or we would be revisiting the same states because of the seed.
        if not counts_do['redo']:
            for _ in range(logger.config['n_runs']):
                logger.config['env'].reset()

        counts = count(logger, n_runs=N)
        logger.update_counts(counts, addn=N)

    if counts_do['redo'] or counts_do['update']:
        logger.dump_results()
        logger.dump_config()

    ### Scores
    if scores_do['redo']:
        print("\n----- Scoring -----\n")
        scores = score(logger)
        logger.update_scores(scores)

    if scores_do['update']:
        already_done = [st for st in args.more_scoretypes if st in logger.config['score_types']]
        if len(already_done) != 0:
            raise Exception("Scoretypes", ",".join(already_done), "already done! Remove them from --more_scoretypes")
        print("\n----- Additional Scores ({}) -----\n".format(args.more_scoretypes))
        scores = score(logger, score_types=args.more_scoretypes)
        logger.update_scores(scores)

    if scores_do['redo'] or scores_do['update']:
        logger.dump_results()
        logger.dump_config()

    ### Interpolation
    if interpol_do['redo']:
        print("\n----- Interpolating -----\n")
        if args.redo_interpol is not None:
            i, t = args.redo_interpol
            logger.config['n_inc'] = i if i >= 0 else logger.config['n_inc']
            logger.config['n_test'] = t if t >= 0 else logger.config['n_test']
        elif logger.config['n_inc'] == -1:
            logger.config['n_inc'] = int(logger.data['logs'][0]['counting_abs_states'] / 10)
        interpol = interpolate(logger)
        logger.update_interpolation(interpol)

    if interpol_do['update']:
        print("\n----- Additional Interpolations ({}) -----\n".format(args.more_scoretypes))
        interpol = interpolate(logger, score_types=args.more_scoretypes)
        logger.update_interpolation(interpol)

    if interpol_do['redo'] or interpol_do['update']:
        logger.dump_results()
        logger.dump_config()

    ### Display results ###
    # Main results
    final = False
    if logger.config['env_name'].startswith('GYM'):
        from elements.envs import GYM_SHORTCUTS
        game = GYM_SHORTCUTS[logger.config['env_name']][3:]
        offsets = {
            'atlantis': 7656.0,
            'breakout': 1.47,
            'pong': -12.77,
            'space_invaders': 142.8,
            'kung_fu_master': 221.0,
            'boxing': -1.84,
            'seaquest': 58.4,
            'chopper_command': 581.0,
        }
        draw_interpol_results(logger, logger.config['score_types'], 0, [1], x_fracs=True, y_fracs=True, smooth=False,
            x_name='States Restored (%)', y_names=['Original Reward (%)'], combine_sbfl=final,
            y_offset=offsets[game])
        draw_interpol_results(logger, logger.config['score_types'], 4, [1], y_fracs=True,
            trans_x=lambda x: 1-x, x_name="Policy's Action Taken (% of Steps)",
            y_names=['Original Reward (%)'], smooth=False, combine_sbfl=final,
            y_offset=offsets[game])
    else:
        draw_interpol_results(logger, logger.config['score_types'], 0, [1], x_fracs=True, y_fracs=True, smooth=False,
            x_name='States Restored (%)', y_names=['Original Reward (%)'], combine_sbfl=final)
        draw_interpol_results(logger, logger.config['score_types'], 4, [1], y_fracs=True,
            trans_x=lambda x: 1-x, x_name="Policy's Action Taken (% of Steps)",
            y_names=['Original Reward (%)'], smooth=False, combine_sbfl=final)

    # score_histogram(logger, logger.config['score_types'])

    # from visualisation.graphing import cartpole_graphs
    # cartpole_graphs(logger.config['pol_name'], logger.data['scores'][0], logger.config['score_types'])

    # Extra
    # draw_interpol_results(logger, logger.config['score_types'], 0, [2, 3], hlines=True)
    # draw_interpol_results(logger, logger.config['score_types'], 0, [4])
    # draw_interpol_results(logger, logger.config['score_types'], 4, [2, 3], hlines=True,
    #     trans_x=lambda x: 1-x, x_name='Proportion of Actions Taken Actively')
    # draw_interpol_results(logger, logger.config['score_types'], 4, [5],
    #     trans_x=lambda x: 1-x, x_name='Proportion of Actions Taken Actively')

if __name__ == '__main__':
    main()
