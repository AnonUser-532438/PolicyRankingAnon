from environments.uber_gym.envspec import get_env
from environments.uber_gym.polspec import get_pol

env = get_env('Breakout-v4', 0, device=None, abst_type=-1, vis_type=-1, max_steps=4000)
pol = get_pol('Breakout-v4', env, None)

s = env.reset()
rew = 0
steps = 0
done = False
while not done:
    a = pol([s], None, None)
    s, r, done, info = env.step(a)
    steps += 1
    rew += r
print(rew)
