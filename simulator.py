import numpy as np
from typing import Dict, Tuple, List, Optional
BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
ANTIGEN_MAP = {'A+': [1, 0, 1], 'A-': [1, 0, 0], 'B+': [0, 1, 1], 'B-': [0, 1, 0], 'AB+': [1, 1, 1], 'AB-': [1, 1, 0], 'O+': [0, 0, 1], 'O-': [0, 0, 0]}
R_GAS = 8.314
E_A = 36000.0
T_REF = 298.15
K_REF = 0.38

def generate_single_sample(blood_group: Optional[str]=None, temp_celsius: float=28.0, hematocrit: float=42.0, is_weak_variant: bool=False, has_bubble_artifact: bool=False, time_steps: int=200, duration_sec: float=10.0, noise_level: float=0.015) -> Dict[str, np.ndarray]:
    if blood_group is None:
        blood_group = np.random.choice(BLOOD_GROUPS)
    t = np.linspace(0, duration_sec, time_steps)
    temp_kelvin = temp_celsius + 273.15
    delta_inv_t = 1.0 / temp_kelvin - 1.0 / T_REF
    k_temp = K_REF * np.exp(-(E_A / R_GAS) * delta_inv_t)
    hct_factor = hematocrit / 45.0
    base_signal = 1.0 / (0.8 + 0.4 * hct_factor)
    antigen_profile = ANTIGEN_MAP[blood_group].copy()
    signals = np.zeros((3, time_steps), dtype=np.float32)
    for ch_idx in range(3):
        reacts = antigen_profile[ch_idx]
        channel_signal = np.full(time_steps, base_signal, dtype=np.float32)
        if reacts:
            rate = k_temp
            asymptote = 0.42 * (1.0 / (0.7 + 0.3 * hct_factor))
            beta = 1.4
            if is_weak_variant and ch_idx in [0, 2]:
                rate = k_temp * 0.4
                asymptote = asymptote * 0.55
                beta = 1.0
            kinetic_drop = asymptote * (1.0 - np.exp(-(rate * t) ** beta))
            channel_signal -= kinetic_drop
            if is_weak_variant and ch_idx in [0, 2]:
                micro_flutter = 0.015 * np.sin(10.0 * t) * (1.0 - np.exp(-rate * t))
                channel_signal += micro_flutter
        else:
            drift = 0.015 * (1.0 - np.exp(-0.08 * t))
            channel_signal -= drift
        channel_signal += np.random.normal(0, noise_level, size=time_steps)
        if has_bubble_artifact and ch_idx == 1:
            bubble_center = int(time_steps * 0.45)
            bubble_span = 12
            channel_signal[bubble_center - bubble_span:bubble_center + bubble_span] -= 0.35
        signals[ch_idx] = channel_signal
    return {'signals': signals, 'blood_group': blood_group, 'class_idx': BLOOD_GROUPS.index(blood_group), 'temperature': np.float32(temp_celsius), 'hematocrit': np.float32(hematocrit), 'is_weak': is_weak_variant, 'is_corrupt': has_bubble_artifact, 'antigen_profile': np.array(antigen_profile, dtype=np.float32)}

def generate_batch(batch_size: int=64, time_steps: int=200) -> Dict[str, np.ndarray]:
    signals_list = []
    class_indices = []
    temps = []
    hcts = []
    antigens = []
    for _ in range(batch_size):
        bg = np.random.choice(BLOOD_GROUPS)
        temp = float(np.random.uniform(10.0, 48.0))
        hct = float(np.random.uniform(18.0, 62.0))
        weak = np.random.rand() < 0.15
        bubble = np.random.rand() < 0.05
        sample = generate_single_sample(blood_group=bg, temp_celsius=temp, hematocrit=hct, is_weak_variant=weak, has_bubble_artifact=bubble, time_steps=time_steps)
        signals_list.append(sample['signals'])
        class_indices.append(sample['class_idx'])
        temps.append(sample['temperature'])
        hcts.append(sample['hematocrit'])
        antigens.append(sample['antigen_profile'])
    return {'signals': np.stack(signals_list), 'class_indices': np.array(class_indices, dtype=np.int64), 'temperatures': np.array(temps, dtype=np.float32), 'hematocrits': np.array(hcts, dtype=np.float32), 'antigens': np.stack(antigens)}
