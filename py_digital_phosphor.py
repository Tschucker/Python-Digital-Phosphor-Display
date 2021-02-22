#Imports
from dearpygui.core import *
from dearpygui.simple import *
import math
import numpy as np
from scipy import interpolate
from rtlsdr import RtlSdr

#Default Variables
fs = 2.048e6
fc = 915e6
fft_len = 4096
fft_div = 8
mag_steps = 300
max_m = 0
min_m = 0
decay = 0.04
sdr_open = False

#FFT Function
def fft_intensity_gui(samples: np.ndarray, fft_len: int = 256, fft_div: int = 2, mag_steps: int = 100):
    
    num_ffts = math.floor(len(samples)/fft_len)
    
    fft_array = []
    for i in range(num_ffts):
        temp = np.fft.fftshift(np.fft.fft(samples[i*fft_len:(i+1)*fft_len]))
        temp_mag = 20.0 * np.log10(np.abs(temp))
        fft_array.append(temp_mag)
        
    max_mag = np.amax(fft_array)
    min_mag = np.abs(np.amin(fft_array))
        
    return(fft_array, max_mag, min_mag)
    
#Open RTLSDR
try:
    sdr = RtlSdr()
    sdr.sample_rate = fs
    sdr.center_freq = fc
    sdr.gain = 'auto'
    sdr_open = True
except:
    print("No RTLSDR found")
    sdr_open = False

#Callbacks
def retune_callback(sender, data):
    global max_m, min_m, sdr, fs, fc
    
    max_m = 0
    min_m = 0
    
    fs = float(get_value("fs"))
    fc = float(get_value("fc"))
    
    sdr.sample_rate = fs
    sdr.center_freq = fc
    
def ig_fft_callback(sender, data):
    global max_m, min_m, sdr, sdr_open
    
    if sdr_open:
        samples = sdr.read_samples(fft_len)
        fft_array, max_mag, min_mag = fft_intensity_gui(samples, fft_len, fft_div, mag_steps)
    
        if max_mag > max_m:
            max_m = max_mag
        if min_mag > min_m:
            min_m = min_mag
        
        norm_fft_array = fft_array
        norm_fft_array[0] = (fft_array[0]+min_m)/(max_m+min_m)
       
        #update data
        hitmap_array = get_data("hitmap")*np.exp(-decay)

        mag_step = 1/mag_steps
        
        for m in range(fft_len):
            hit_mag = int(norm_fft_array[0][m]/mag_step)
            hitmap_array[hit_mag][int(m/fft_div)] = hitmap_array[hit_mag][int(m/fft_div)] + .8  
    
        max_hit = np.amax(hitmap_array)/2
    
        add_heat_series("Spectrum", "", hitmap_array, (mag_steps+1), (int(fft_len/fft_div)), 0, max_hit, format='')
        add_data("hitmap", hitmap_array)
    
def fft_plus_callback(sender, data):
    global fft_len, fft_div, mag_steps
    
    temp = int(np.log2(fft_len))
    fft_len = int(2**(temp+1))
    fft_div = int(fft_div*2)
    hitmap_array = np.random.random((mag_steps+1,int(fft_len/fft_div)))*np.exp(-10)   
    add_data("hitmap", hitmap_array)
    set_value("fft_size", str(fft_len))
         
def fft_min_callback(sender, data):
    global fft_len, fft_div, mag_steps
    
    temp = int(np.log2(fft_len))
    fft_len = int(2**(temp-1))
    fft_div = int(fft_div/2)
    hitmap_array = np.random.random((mag_steps+1,int(fft_len/fft_div)))*np.exp(-10)   
    add_data("hitmap", hitmap_array)
    set_value("fft_size", str(fft_len))
    
def time_plus_callback(sender, data):
    global decay
    
    decay = decay/2
    set_value("per_decay", str(decay))
    
def time_min_callback(sender, data):
    global decay
    
    decay = decay*2
    set_value("per_decay", str(decay))
       
def set_color_viridis_callback(sender, data):
    set_color_map("Spectrum", 5)    
def set_color_plasma_callback(sender, data):
    set_color_map("Spectrum", 6)
def set_color_hot_callback(sender, data):
    set_color_map("Spectrum", 7)
def set_color_pink_callback(sender, data):
    set_color_map("Spectrum", 9)
def set_color_jet_callback(sender, data):
    set_color_map("Spectrum", 10)
    
def close_gui_callback(sender, data):
    stop_dearpygui()
    
#GUI
with window("Settings", width=300, height=500):
    set_window_pos("Settings", 700, 0)
    add_text("RTLSDR Tuning")
    add_input_text("fs", default_value=str(fs))
    add_input_text("fc", default_value=str(fc))
    add_button("Retune", callback=retune_callback)
    add_text("FFT Resolution")
    with group("updown1", horizontal=True):
        add_button("FFT +", label="+", callback=fft_plus_callback)
        add_button("FFT -", label="-", callback=fft_min_callback)
    add_label_text("fft_size", label="FFT Length", default_value=str(fft_len))
    add_text("Persistance")
    with group("updown2", horizontal=True):
        add_button("Time +", label="+", callback=time_plus_callback)
        add_button("Time -", label="-", callback=time_min_callback)
    add_label_text("per_decay", label="Decay", default_value=str(decay))
    
    
    
with window("Py-Digital Phosphor", width=700, height=500):
    set_window_pos("Py-Digital Phosphor", 0, 0)
    add_plot("Spectrum", height=-1, yaxis_invert=True, xaxis_no_tick_labels=True, yaxis_no_tick_labels=True)
    set_color_map("Spectrum", 6)
    
    hitmap_array = np.random.random((mag_steps+1,int(fft_len/fft_div)))*np.exp(-10)
    add_data("hitmap", hitmap_array)
    
    with menu_bar("Main Menu Bar"):
        with menu("Main"):
            with menu("Color Map"):
                add_menu_item("Plasma", callback=set_color_plasma_callback)
                add_menu_item("Hot", callback=set_color_hot_callback)
                add_menu_item("Viridis", callback=set_color_viridis_callback)
                add_menu_item("Jet", callback=set_color_jet_callback)
                add_menu_item("Pink", callback=set_color_pink_callback)
            
    set_render_callback(ig_fft_callback)

if not sdr_open:
    with window("RTLSDR Error", width=1000, height=500):
        set_window_pos("RTLSDR Error", 0, 0)
        add_text("No RTLSDR device was found")
        add_button("Exit", callback=close_gui_callback)
    
start_dearpygui()

#Close SDR
if sdr_open:
    sdr.close()