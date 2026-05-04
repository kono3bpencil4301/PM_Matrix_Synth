import numpy as np
from scipy.io.wavfile import write
import Matrix_DX7
import Config
import Env


class Operator:
    def __init__(self, name, frequency, amplitude, phase, volume, modulation_index, ratio):
        self.name = name
        self.frequency = frequency
        self.amplitude = amplitude
        self.phase = phase
        self.volume = volume
        self.modulation_index = 0.0
        self.ratio = ratio

    def __init_Env__(self, name, frequency, amplitude, phase, volume, modulation_index):
        self.Volume_Env = Config.OPs_Volume_Envs_Matrix[self.name]
        self.Mod_Env = Config.OPs_Mod_Envs_Matrix[self.name]


def Get_Mod_Matrix(Carrier_OP_index, Modulator_OP_index):
    return Matrix_DX7.Mod_Matrix[Modulator_OP_index][Carrier_OP_index]


def Get_OP_Envelope_Matrix(OP_index):
    return Config.OPs_Volume_Envs_Matrix[OP_index], Config.OPs_Mod_Envs_Matrix[OP_index]


def Get_Modulation_Index(Carrier_OP_index, Modulator_OP_index):
    return Matrix_DX7.Mod_Matrix[Modulator_OP_index][Carrier_OP_index]


def Set_Modulation_Index(Carrier_OP_index, Modulator_OP_index, modulation_index):
    Matrix_DX7.Mod_Matrix[Modulator_OP_index][Carrier_OP_index] = modulation_index
    return Matrix_DX7.Mod_Matrix[Modulator_OP_index][Carrier_OP_index]


def Set_OP_Volume_Envelope(OP_index, Volume_Env):
    Config.OPs_Volume_Envs_Matrix[OP_index] = Volume_Env
    return Config.OPs_Volume_Envs_Matrix[OP_index]


def Set_OP_Modulation_Envelope(OP_index, Mod_Env):
    Config.OPs_Mod_Envs_Matrix[OP_index] = Mod_Env
    return Config.OPs_Mod_Envs_Matrix[OP_index]


def Get_Carrier_OP_and_Modulator_OPs(Carrier_OP_index, Modulator_OP_index, Matrix_DX7):
    Carrier = Carrier_OP_index
    Modulators = []
    for i in range(6):
        if Matrix_DX7.Mod_Matrix[i][Carrier_OP_index] != 0:
            Modulators.append(i)
    return Carrier, Modulators


def PM_Synthesis(
    Carrier_OP_index,
    Modulator_OP_index,
    phase,
    frequency,
    amplitude,
    sample_rate,
    freq_ratios,
    duration,
    Get_Modulation_Index,
    Get_OP_Envelope_Matrix,
):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    waveform = np.zeros_like(t)

    total_modulation = np.zeros_like(t)

    for i in range(6):
        if i in Modulator_OP_index:
            adsr_params = Get_OP_Envelope_Matrix(i)[1]
            mod_env = Env.Envelope(*adsr_params).generate(duration, sample_rate)
            modulation_index = Get_Modulation_Index(Carrier_OP_index, i)

            mod_waveform = modulation_index * np.sin(
                2 * np.pi * frequency[i] * t + phase[i]
            )
            total_modulation += mod_waveform * mod_env

    for i in range(6):
        if i == Carrier_OP_index:
            adsr_params = Get_OP_Envelope_Matrix(i)[0]
            volume_env = Env.Envelope(*adsr_params).generate(duration, sample_rate)

            carrier_phase = 2 * np.pi * frequency[i] * t + phase[i] + total_modulation
            op_waveform = amplitude[i] * np.sin(carrier_phase)

            waveform = op_waveform * volume_env

    return waveform


Operators = []

for i in range(6):
    op = Operator(
        f"OP{i + 1}",
        Config.frequency[i],
        Config.amplitude[i],
        Config.phases[i],
        Config.volume[i],
        Config.freq_ratios[i],
        0.0,
    )
    Operators.append(op)


def generate_waveform(duration, sample_rate):
    total_samples = int(sample_rate * duration)

    mod_matrix = np.array(Matrix_DX7.Mod_Matrix, dtype=np.float64)
    freq = np.array(Config.frequency, dtype=np.float64)
    amp = np.array(Config.amplitude, dtype=np.float64)
    vol = np.array(Config.volume, dtype=np.float64)
    freq_ratios = np.array(Config.freq_ratios, dtype=np.float64)

    volume_envs = []
    mod_envs = []
    for i in range(6):
        vol_adsr = Config.OPs_Volume_Envs_Matrix[i]
        mod_adsr = Config.OPs_Mod_Envs_Matrix[i]
        vol_env = Env.Envelope(*vol_adsr)
        mod_env = Env.Envelope(*mod_adsr)
        volume_envs.append(vol_env.generate(duration, sample_rate))
        mod_envs.append(mod_env.generate(duration, sample_rate))

    phases = np.zeros(6, dtype=np.float64)
    phase_steps = 2 * np.pi * freq * freq_ratios / sample_rate

    previous_outputs = np.zeros(6, dtype=np.float64)
    audio = np.zeros(total_samples, dtype=np.float64)

    for n in range(total_samples):
        current_outputs = np.zeros(6, dtype=np.float64)

        for target in range(6):
            mod_input = 0.0
            for source in range(6):
                mod_input += (
                    previous_outputs[source]
                    * mod_matrix[source][target]
                    * mod_envs[source][n]
                )

            current_outputs[target] = amp[target] * np.sin(phases[target] + mod_input)
            phases[target] += phase_steps[target]

        audio[n] = np.sum(current_outputs * vol * [env[n] for env in volume_envs])
        previous_outputs = current_outputs

    return audio


waveform = generate_waveform(Config.duration, Config.sample_rate)
waveform = np.int16(waveform / np.max(np.abs(waveform)) * 32767)
write("output.wav", Config.sample_rate, waveform)
print("音频已生成并保存为 output.wav")
