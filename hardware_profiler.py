import os
import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Any
from models import TCECOModel

def profile_tceco_hardware(device_freq_mhz: float=240.0, operating_voltage_v: float=3.3, active_current_ma: float=80.0) -> Dict[str, Any]:
    model = TCECOModel(time_steps=200, out_classes=8)
    total_params = sum((p.numel() for p in model.parameters()))
    fp32_kb = total_params * 4 / 1024.0
    int8_kb = total_params * 1 / 1024.0
    total_macs = 67200 + 512000 + 614400 + 2304
    total_flops = total_macs * 2
    peak_activation_sram_kb = 64 * 50 * 4 * 2 / 1024.0
    total_sram_needed_kb = peak_activation_sram_kb + int8_kb
    total_cpu_cycles = total_macs * 1.8
    inference_time_ms = total_cpu_cycles / (device_freq_mhz * 1000000.0) * 1000.0
    power_watts = operating_voltage_v * (active_current_ma / 1000.0)
    energy_joules_per_test = power_watts * (inference_time_ms / 1000.0)
    energy_mj_per_test = energy_joules_per_test * 1000.0
    battery_joules = 1.2 * 3.7 * 3600.0
    total_tests_on_single_charge = int(battery_joules / (energy_joules_per_test + 1e-06))
    return {'target_microcontroller': 'ESP32-WROOM-32 (Xtensa Dual-Core 32-bit @ 240MHz)', 'hardware_cost_inr': '₹380 - ₹450 ($4.80 - $5.50 USD)', 'trainable_parameters': total_params, 'flash_storage_int8_kb': round(int8_kb, 2), 'flash_storage_fp32_kb': round(fp32_kb, 2), 'peak_sram_footprint_kb': round(total_sram_needed_kb, 2), 'available_esp32_sram_kb': 520, 'sram_utilization_percent': round(total_sram_needed_kb / 520.0 * 100.0, 2), 'total_macs': total_macs, 'total_flops': total_flops, 'estimated_edge_latency_ms': round(inference_time_ms, 2), 'power_consumption_mw': round(power_watts * 1000.0, 1), 'energy_per_test_mj': round(energy_mj_per_test, 3), 'tests_per_1200mah_charge': total_tests_on_single_charge}
if __name__ == '__main__':
    report = profile_tceco_hardware()
    print('=' * 80)
    print('        CYBER-PHYSICAL HARDWARE & ENERGY PROFILER (TINYML BENCHMARK)')
    print('=' * 80)
    for k, v in report.items():
        print(f"  • {k.replace('_', ' ').title():<32} : {v}")
    print('=' * 80)
