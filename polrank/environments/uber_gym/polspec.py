import random

import tensorflow as tf
from atari_zoo import MakeAtariModel
from lucid.optvis.render import import_model

from elements.policies import AbstractPol

def get_pol(name, env, device, **kwargs):
    name += "NoFrameskip-v4"

    m = MakeAtariModel('rainbow', name, 1)()
    m.load_graphdef()
    nA = env.action_space()
    obs_shape = list(env.observation_space())
    return RainbowAgent(m, nA, obs_shape)

class RainbowAgent(AbstractPol):
    def __init__(self, pol, nA, obs_shape):
        super().__init__(pol)
        self.nA = nA
        config = tf.ConfigProto(
                device_count = {'GPU': 1}
            )
        config.gpu_options.allow_growth=True
        self.sess = tf.Session(config=config)

        self.X_t = tf.placeholder(tf.float32, [None] + obs_shape)
        T = import_model(self.pol, self.X_t, self.X_t)
        self.action_sample = self.pol.get_action(T)

    def __call__(self, states, actions, rews):
        if random.random() < 0.01:
            act = random.randint(0,self.nA-1)
        else:
            train_dict = {self.X_t:states[-1][0][None]}
            results = self.sess.run([self.action_sample], feed_dict=train_dict)
            act = results[0]
        return act
