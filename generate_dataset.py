import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from simulator import generate_batch, BLOOD_GROUPS

def generate_and_save_dataset(n_samples: int=5000):
    dataset_dir = os.path.join(os.path.dirname(__file__), 'dataset')
    os.makedirs(dataset_dir, exist_ok=True)
    print(f'[+] Generating {n_samples:,} Diverse Patient Blood Samples...')
    batch_size = 500
    num_batches = n_samples // batch_size
    all_signals = []
    all_bgs = []
    all_temps = []
    all_hcts = []
    all_antigens = []
    for b in range(num_batches):
        batch = generate_batch(batch_size=batch_size, time_steps=200)
        all_signals.append(batch['signals'])
        for idx in batch['class_indices']:
            all_bgs.append(BLOOD_GROUPS[idx])
        all_temps.append(batch['temperatures'])
        all_hcts.append(batch['hematocrits'])
        all_antigens.append(batch['antigens'])
        print(f'  -> Generated {len(all_bgs):,}/{n_samples:,} samples...')
    signals_array = np.concatenate(all_signals, axis=0)
    temps_array = np.concatenate(all_temps, axis=0)
    hcts_array = np.concatenate(all_hcts, axis=0)
    antigens_array = np.concatenate(all_antigens, axis=0)
    signals_file = os.path.join(dataset_dir, 'raw_sensor_signals.npy')
    np.save(signals_file, signals_array)
    print(f'[+] Saved full 3-channel time-series trajectories to: {signals_file}')
    csv_file = os.path.join(dataset_dir, 'blood_samples.csv')
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write('Patient_ID,Blood_Group,Ambient_Temp_C,Hematocrit_Percent,Channel_A_Agglutination,Channel_B_Agglutination,Channel_D_Rh_Agglutination,Channel_A_Drop_mV,Channel_B_Drop_mV,Channel_D_Drop_mV\n')
        for i in range(n_samples):
            p_id = f'PATIENT_{i + 1:05d}'
            bg = all_bgs[i]
            temp = temps_array[i]
            hct = hcts_array[i]
            ant_a = int(antigens_array[i][0])
            ant_b = int(antigens_array[i][1])
            ant_d = int(antigens_array[i][2])
            drop_a = (signals_array[i, 0, :15].mean() - signals_array[i, 0, -1]) * 1000.0
            drop_b = (signals_array[i, 1, :15].mean() - signals_array[i, 1, -1]) * 1000.0
            drop_d = (signals_array[i, 2, :15].mean() - signals_array[i, 2, -1]) * 1000.0
            f.write(f'{p_id},{bg},{temp:.1f},{hct:.1f},{ant_a},{ant_b},{ant_d},{drop_a:.1f},{drop_b:.1f},{drop_d:.1f}\n')
    print(f'[+] Saved structured patient metadata table to: {csv_file}')
    csv_size_kb = os.path.getsize(csv_file) / 1024.0
    npy_size_mb = os.path.getsize(signals_file) / (1024.0 * 1024.0)
    print(f'[+] Dataset Export Complete! CSV Size: {csv_size_kb:.2f} KB | Sensor Data: {npy_size_mb:.2f} MB')
if __name__ == '__main__':
    generate_and_save_dataset(n_samples=5000)
