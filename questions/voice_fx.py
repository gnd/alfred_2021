from pedalboard import *
from pedalboard.io import AudioFile

def b_delay(audio, samplerate):
    b = Pedalboard([
        # Compressor(),
        Delay(delay_seconds=0.125, feedback=0.30),
        # Reverb(0.5),
        Gain(gain_db=5),
    ])
    return b(audio, samplerate)

def b_hell(audio, samplerate):
    b = Pedalboard([
        Compressor(),
        PitchShift(semitones=-12),
        Phaser(rate_hz=10000, depth=2000),
        # Distortion(6),
        # Bitcrush(1.5),
        Distortion(2.5),
        Bitcrush(4.3),
        Resample(10000, Resample.Quality.ZeroOrderHold),
        Reverb(1, 1, 1, 0.8, 1, freeze_mode=1),
    ])

    return b(audio, samplerate)

def make_b_decay(decay_level):
    decay_level = decay_level + 1

    def board(audio, samplerate):
        print(decay_level)
        b = Pedalboard([
            Compressor(),
            # PitchShift(semitones=-12),
            # Phaser(rate_hz=10000 / decay_level, depth=2000 / decay_level),
            # Distortion(6),
            # Bitcrush(1.5),
            Distortion(decay_level * 10),
            Bitcrush(32 / decay_level),
            Resample(441000 / decay_level, Resample.Quality.ZeroOrderHold),
            Reverb(
                min(decay_level * 0.05, 1),
                min(decay_level * 0.05, 1),
                min(decay_level * 0.05, 1),
                1,
                min(decay_level * 0.05, 1))
        ])

        return b(audio, samplerate)

    return board



def board(audio, samplerate):
    return b_hell

def apply_fx(board=board, fname="output.wav", fname_out="output_fx.wav"):
    with AudioFile(fname, 'r') as f:
        audio = f.read(f.frames)
        samplerate = f.samplerate

    effected = board(audio, samplerate)

    with AudioFile(fname_out, 'w', samplerate, effected.shape[0]) as f:
        f.write(effected)