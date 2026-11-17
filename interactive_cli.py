import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from simulator import BLOOD_GROUPS
from run_demo import load_system, evaluate_patient

def interactive_mode():
    model, auditor = load_system()
    print('\n' + '=' * 60)
    print('      T-CECO INTERACTIVE POINT-OF-CARE DIAGNOSTICS')
    print('=' * 60)
    print(f"Available Blood Groups: {', '.join(BLOOD_GROUPS)}")
    while True:
        try:
            print("\n[+] Enter Patient Parameters (or type 'exit' to quit):")
            bg_input = input('  1. Select Blood Group (e.g. A+, B-, O+, AB+): ').strip().upper()
            if bg_input in ['EXIT', 'QUIT', 'Q']:
                break
            if bg_input not in BLOOD_GROUPS:
                print(f"  [-] Invalid blood group '{bg_input}'. Choose from {BLOOD_GROUPS}")
                continue
            temp_input = input('  2. Ambient Temperature in °C [Default: 28.0]: ').strip()
            temp = float(temp_input) if temp_input else 28.0
            hct_input = input('  3. Patient Hematocrit % (18=Severe Anemia, 45=Normal) [Default: 42.0]: ').strip()
            hct = float(hct_input) if hct_input else 42.0
            weak_input = input('  4. Simulate Weak D / A2 Subtype? (y/n) [Default: n]: ').strip().lower()
            weak = weak_input == 'y'
            evaluate_patient(model=model, auditor=auditor, blood_group=bg_input, temp=temp, hct=hct, weak=weak, bubble=False, label=f'Custom Interactive Test ({bg_input})')
        except (KeyboardInterrupt, EOFError):
            break
        except Exception as e:
            print(f'  [-] Error: {e}')
if __name__ == '__main__':
    interactive_mode()
