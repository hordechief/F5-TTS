from flask import Flask, request, jsonify
import subprocess
import os
from importlib.resources import files
import tqdm
import random, sys
import torchaudio
import time
from pathlib import Path

from src.f5_tts.api import F5TTS

from f5_tts.model.utils import seed_everything

from f5_tts.infer.utils_infer import (
    hop_length,
    infer_process,
    load_model,
    load_vocoder,
    preprocess_ref_audio_text,
    remove_silence_for_generated_wav,
    save_spectrogram,
    target_sample_rate,
    chunk_text,
    infer_batch_process,
)
app = Flask(__name__)

f5tts = F5TTS()

start_time = time.time()
data_dir = os.environ.get("DATA_DIR",'./data/tts')
output_dir = os.environ.get("OUTPUT_DIR",'./output')
ref_sound_name = os.environ.get("REF_SOUND", "hordechief.mp3") # "trump.mp3"
print(f">>>>Data dir is {data_dir}, Output dir is {output_dir}, Ref sound is {ref_sound_name}")
ref_file= str(Path(data_dir) / ref_sound_name)

ref_text=""
ref_file, ref_text = preprocess_ref_audio_text(ref_file, ref_text, device=f5tts.device)
end_time = time.time()
print("\n--------------------------------------------------------")
print(f"preprocess_ref_audio_text Execution time: {end_time - start_time:.2f} seconds")


@app.route('/process', methods=['POST'])
def process_file():
    input_file = request.json.get('input_file')

    try:
        result = subprocess.run(['python', 'src/f5_tts/api.py', '--text', input_file], capture_output=True, text=True)

        if result.returncode != 0:
            return jsonify({'error': 'Script execution failed', 'output': result.stderr}), 500
        
        # output_audio_path = 'tests/api_out.wav'
        output_audio_path = str(Path(output_dir) / 'api_out.wav')

        return jsonify({'audio_file': output_audio_path}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/infer', methods=['POST'])
def process_file_infer():
    text = request.json.get('input_file')

    try:
        # -------------------- f5tts.infer ----------------------
        # wav, sr, spect = f5tts.infer(
        #     ref_file="./data/tts/hordechief.mp3",
        #     ref_text="",
        #     gen_text=text,
        #     file_wave=str(files("f5_tts").joinpath("./output/api_out.wav")),
        #     file_spect=str(files("f5_tts").joinpath("./output/api_out.png")),
        #     seed=-1,  # random seed = -1
        # )

        seed = random.randint(0, sys.maxsize)
        seed_everything(seed)
        f5tts.seed = seed

        # ref_file="./data/tts/hordechief.mp3"
        # ref_text=""
        gen_text=text
        file_wave=str(Path(output_dir) / 'api_out.wav')
        file_spect=str(Path(output_dir) / 'api_out.png')
        print(f">>>file_wave is {file_wave}, file_spect is {file_spect}")
        show_info=print
        progress=tqdm
        target_rms=0.1
        cross_fade_duration=0.15
        sway_sampling_coef=-1
        cfg_strength=2
        nfe_step=32
        speed=1.0
        fix_duration=None
        remove_silence=False

        # ref_file, ref_text = preprocess_ref_audio_text(ref_file, ref_text, device=f5tts.device)

        USE_INFER__PROCESS = True
        if USE_INFER__PROCESS:
            wav, sr, spect = infer_process(
                ref_file,
                ref_text,
                gen_text,
                f5tts.ema_model,
                f5tts.vocoder,
                f5tts.mel_spec_type,
                show_info=show_info,
                progress=progress,
                target_rms=target_rms,
                cross_fade_duration=cross_fade_duration,
                nfe_step=nfe_step,
                cfg_strength=cfg_strength,
                sway_sampling_coef=sway_sampling_coef,
                speed=speed,
                fix_duration=fix_duration,
                device=f5tts.device,
            )
        else:
            start_time = time.time()
            # Split the input text into batches
            audio, sr = torchaudio.load(ref_file)
            max_chars = int(len(ref_text.encode("utf-8")) / (audio.shape[-1] / sr) * (25 - audio.shape[-1] / sr))
            gen_text_batches = chunk_text(gen_text, max_chars=max_chars)
            for i, gen_text in enumerate(gen_text_batches):
                print(f"gen_text {i}", gen_text)
            end_time = time.time()
            print("\n--------------------------------------------------------")
            print(f"chunk_text Execution time: {end_time - start_time:.2f} seconds")

            show_info(f"Generating audio in {len(gen_text_batches)} batches...")

            start_time = time.time()
            wav, sr, spect =  infer_batch_process(
                (audio, sr),
                ref_text,
                gen_text_batches,
                f5tts.ema_model,
                f5tts.vocoder,
                mel_spec_type=f5tts.mel_spec_type,
                progress=progress,
                target_rms=target_rms,
                cross_fade_duration=cross_fade_duration,
                nfe_step=nfe_step,
                cfg_strength=cfg_strength,
                sway_sampling_coef=sway_sampling_coef,
                speed=speed,
                fix_duration=fix_duration,
                device=f5tts.device,
            )        
            end_time = time.time()
            print("\n--------------------------------------------------------")
            print(f"infer_batch_process Execution time: {end_time - start_time:.2f} seconds")        

        # export_wav
        start_time = time.time()
        if file_wave is not None:
            f5tts.export_wav(wav, file_wave, remove_silence)
        end_time = time.time()
        print("\n--------------------------------------------------------")
        print(f"export_wav Execution time: {end_time - start_time:.2f} seconds")            

        # export_spectrogram
        start_time = time.time()
        if file_spect is not None:
            f5tts.export_spectrogram(spect, file_spect)
        end_time = time.time()
        print("\n--------------------------------------------------------")
        print(f"export_spectrogram Execution time: {end_time - start_time:.2f} seconds")            
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    output_audio_path = str(Path(output_dir) / 'api_out.wav')

    return jsonify({'audio_file': output_audio_path}), 200

    print("seed :", f5tts.seed)

if __name__ == '__main__':
    PORT = os.environ.get("PORT", 8890)
    app.run(debug=True, host='0.0.0.0', port=int(PORT))
