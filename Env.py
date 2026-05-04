import numpy as np


class Envelope:
    def __init__(self, attack=0.1, decay=0.2, sustain=0.6, release=0.4):
        self.attack = attack
        self.decay = decay
        self.sustain = sustain
        self.release = release

    def generate(self, duration, sample_rate=44100):
        total_samples = int(sample_rate * duration)
        env = np.zeros(total_samples)

        attack_samples = int(sample_rate * self.attack)
        decay_samples = int(sample_rate * self.decay)
        release_samples = int(sample_rate * self.release)

        if attack_samples > 0:
            env[:attack_samples] = np.linspace(0, 1, attack_samples)

        decay_end = attack_samples + decay_samples
        if decay_samples > 0:
            env[attack_samples:decay_end] = np.linspace(1, self.sustain, decay_samples)

        if release_samples > 0:
            env[decay_end:-release_samples] = self.sustain
        else:
            env[decay_end:] = self.sustain

        if release_samples > 0:
            env[-release_samples:] = np.linspace(self.sustain, 0, release_samples)

        return env
