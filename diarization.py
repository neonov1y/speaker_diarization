from pyannote.audio import Pipeline
from pyannote.audio.pipelines.utils.hook import ProgressHook
import torch
import time
import torchaudio
import os
import wave
import numpy as np
import json
import logging
import sys


# Variables
path_yaml = "config_model.yaml"
path_conf = "config_params.json"
path_ffmpeg = "/usr/bin/ffmpeg"
path_log = 'running.log'
path_csv = 'report.csv'
json_data = {}
min_duration = 0.5

speaker1_start = []
speaker1_end = []
speaker2_start = []
speaker2_end = []
overlap_start = []
overlap_end = []
csv_report = ""

# min_duration_off - controls whether intra-speaker pauses are filled. This usually depends on the downstream application
# so it is better to first force it to zero (i.e. never fill intra-speaker pauses) during optimization.
params = {
    'clustering': {
        'method': 'centroid',
        'min_cluster_size': 12,
        'threshold': 0.7045654963945799
    },
    'segmentation': {
        'min_duration_off': 1.0
    }
}

path_in = ''
path_16 = "audio_16K_mono_in.wav"
path_orig = "audio_16K_mono_orig.wav"
path_after_cut_dir = "result_dir"
num_speakers = 2

def print_help():
    print("Usage example: python3 script_name.py -f <input_file>")
    print("\tInput file should be in format of mp4 or wav.")

def input_parser():
    global path_in

    file_flag = 0
    print("Input arguments parsing:")

    if len(sys.argv) < 2:
        print("\tWrong usage, not enough input arguments.")
        print_help()
        exit(1)

    for i in range(0,len(sys.argv)):
        # Processing help message (-h, --help)
        if sys.argv[i] == "-h" or sys.argv[i] == "--help":
            print_help()
            exit(1)

        # Processing input file (-f <file_name>)
        if sys.argv[i] == "-f":
            print("\tInput file detection:")
            if i + 1 < len(sys.argv) and sys.argv[i+1][0] != "-":
                path_in = sys.argv[i+1]
                if os.path.isfile(path_in):
                    print(f"\t\tInput file detected: {path_in}")
                    file_flag = 1
                else:
                    print(f"\t\tNo such file: {path_in}")
                    exit(1)
                path_in = path_in.replace(" ","\\ ")
            elif i == len(sys.argv)-1 or (i + 1 < len(sys.argv) and sys.argv[i+1][0] == "-"):
                print("\t\tMissed input file path!")
                print_help()
                exit(1)

    if file_flag == 0:
        print("\t\tPlease, set input file path!")
        print_help()
        exit(1)

    if path_in[-3:].lower() == "wav" or path_in[-3:].lower() == "mp4":
        print(f"\tFormat of input file is: {path_in[-3:].lower()}")
    else:
        print("\tThe format file is incorrect. Please use wav or mp4 format for input file.")
        print(f"\tFormat of input file is: {path_in[-3:].lower()}")
        exit(1)


def config_parser():
    global json_data, path_ffmpeg, path_yaml, min_duration

    with open(path_conf ) as json_file:
        json_data = json.load(json_file)
        if "path_ffmpeg" in json_data:
            path_ffmpeg = json_data["path_ffmpeg"]
            print("json parser: path_ffmpeg updated to:", path_ffmpeg)
            logging.info(f"json parser: path_ffmpeg updated to: {path_ffmpeg}")
        if "path_yaml" in json_data:
            path_yaml = json_data["path_yaml"]
            print("json parser: path_yaml updated to:", path_yaml)
            logging.info(f"json parser: path_yaml updated to: {path_yaml}")
        if "min_duration" in json_data:
            min_duration = json_data["min_duration"]
            print("json parser: min_duration updated to:", min_duration)
            logging.info(f"json parser: min_duration updated to: {min_duration}")


def process_time_stamps():
    global overlap_start, overlap_end, speaker2_start, speaker2_end, speaker1_start, speaker1_end

    start_index = 0
    stop_flag = 0
    while stop_flag == 0:
        skip_flag = 0
        for i in range(start_index, len(speaker1_start)):
            start_time = float(speaker1_start[i])
            end_time = float(speaker1_end[i])

            for j in range(0, len(speaker2_start)):
                s_time = float(speaker2_start[j])
                e_time = float(speaker2_end[j])

                if start_time < s_time < end_time:
                    skip_flag = 1
                    start_index = i
                    if end_time > e_time:
                        speaker1_end.insert(i, s_time)
                        speaker1_start.insert(i + 1, e_time)
                        overlap_start.append(s_time)
                        overlap_end.append(e_time)
                        del speaker2_start[j]
                        del speaker2_end[j]
                    else:
                        speaker1_end[i] = s_time
                        speaker2_start[j] = end_time
                        overlap_start.append(s_time)
                        overlap_end.append(end_time)
                    break

            if skip_flag == 1:
                break
            if i == (len(speaker1_start) - 1):
                stop_flag = 1

    start_index = 0
    stop_flag = 0
    while stop_flag == 0:
        skip_flag = 0
        for i in range(start_index, len(speaker2_start)):
            start_time = float(speaker2_start[i])
            end_time = float(speaker2_end[i])

            for j in range(0, len(speaker1_start)):
                s_time = float(speaker1_start[j])
                e_time = float(speaker1_end[j])

                if start_time < s_time < end_time:
                    skip_flag = 1
                    start_index = i
                    if end_time > e_time:
                        speaker2_end.insert(i, s_time)
                        speaker2_start.insert(i + 1, e_time)
                        overlap_start.append(s_time)
                        overlap_end.append(e_time)
                        del speaker1_start[j]
                        del speaker1_end[j]
                    else:
                        speaker2_end[i] = s_time
                        speaker1_start[j] = end_time
                        overlap_start.append(s_time)
                        overlap_end.append(end_time)
                    break

            if skip_flag == 1:
                break
            if i == (len(speaker2_start) - 1):
                stop_flag = 1

    overlap_start = sorted(overlap_start)
    overlap_end = sorted(overlap_end)

def create_audio_cuts():
    global csv_report

    # Create directories if not exist
    os.makedirs(path_after_cut_dir, exist_ok=True)
    os.makedirs(path_after_cut_dir + "/speaker1", exist_ok=True)
    os.makedirs(path_after_cut_dir + "/speaker2", exist_ok=True)
    os.makedirs(path_after_cut_dir + "/overlap", exist_ok=True)

    csv_report += (f"File ID for speaker,Speaker Identifier,Start Time (sec),End Time (sec),Total Duration (sec),"
                   f"File Name,Short Audio Flag (less than {min_duration})\n")

    # Files preparation
    for i in range(0, len(speaker1_start)):
        start_time = speaker1_start[i]
        end_time = speaker1_end[i]
        sufix = ""
        short_flag = 0
        silence_flag = 0

        if end_time - start_time <= min_duration:
            print("[info] speaker1 value skipped - to short:", end_time - start_time)
            logging.info(f"[info] speaker1 value skipped - to short: {end_time - start_time}")
            sufix = "_short"
            short_flag = 1
            #continue
        if end_time - start_time <= 0:
            continue

        csv_report += f"{i},speaker1,{start_time},{end_time},{(end_time - start_time):.1f},speaker1_{str(i) + sufix}.wav,{short_flag}\n"

        print(f"[info] command: {path_ffmpeg} -i {path_orig} -ss {start_time} -to {end_time} {path_after_cut_dir}/speaker1/speaker1_{str(i) + sufix}.wav -y -v error")
        logging.info(f"[info] command: {path_ffmpeg} -i {path_orig} -ss {start_time} -to {end_time} {path_after_cut_dir}/speaker1/speaker1_{str(i) + sufix}.wav -y -v error")
        os.system(f"{path_ffmpeg} -i {path_orig} -ss {start_time} -to {end_time} {path_after_cut_dir}/speaker1/speaker1_{str(i) + sufix}.wav -y -v error")

    for i in range(0, len(speaker2_start)):
        start_time = speaker2_start[i]
        end_time = speaker2_end[i]
        sufix = ""
        short_flag = 0
        silence_flag = 0

        if end_time - start_time <= min_duration:
            print("[info] speaker2 value skipped - to short:", end_time - start_time)
            logging.info(f"[info] speaker2 value skipped - to short: {end_time - start_time}")
            sufix = "_short"
            short_flag = 1
        if end_time - start_time <= 0:
            continue

        csv_report += f"{i},speaker2,{start_time},{end_time},{(end_time - start_time):.1f},speaker2_{str(i) + sufix}.wav,{short_flag}\n"

        print(f"[info] command: {path_ffmpeg} -i {path_orig} -ss {start_time} -to {end_time} {path_after_cut_dir}/speaker2/speaker2_{str(i) + sufix}.wav -y -v error")
        logging.info(f"[info] command: {path_ffmpeg} -i {path_orig} -ss {start_time} -to {end_time} {path_after_cut_dir}/speaker2/speaker2_{str(i) + sufix}.wav -y -v error")
        os.system(f"{path_ffmpeg} -i {path_orig} -ss {start_time} -to {end_time} {path_after_cut_dir}/speaker2/speaker2_{str(i) + sufix}.wav -y -v error")

    for i in range(0, len(overlap_start)):
        start_time = overlap_start[i]
        end_time = overlap_end[i]
        sufix = ""
        short_flag = 0
        silence_flag = 0

        if end_time - start_time <= min_duration:
            print("[info] overlap value skipped - to short:", end_time - start_time)
            logging.info(f"[info] overlap value skipped - to short: {end_time - start_time}")
            sufix = "_short"
            short_flag = 1
            #continue
        if end_time - start_time <= 0:
            continue

        csv_report += f"{i},overlap,{start_time},{end_time},{(end_time - start_time):.1f},overlap_{str(i) + sufix}.wav,{short_flag}\n"

        print(f"[info] command: {path_ffmpeg} -i {path_orig} -ss {start_time} -to {end_time} {path_after_cut_dir}/overlap/overlap_{str(i) + sufix}.wav -y -v error")
        logging.info(f"[info] command: {path_ffmpeg} -i {path_orig} -ss {start_time} -to {end_time} {path_after_cut_dir}/overlap/overlap_{str(i) + sufix}.wav -y -v error")
        os.system(f"{path_ffmpeg} -i {path_orig} -ss {start_time} -to {end_time} {path_after_cut_dir}/overlap/overlap_{str(i) + sufix}.wav -y -v error")

    csv_file = open(path_after_cut_dir + "/" + path_csv, "w")
    csv_file.write(csv_report)
    csv_file.close()


def speaker_diar():
    global csv_report, speaker1_start, speaker1_end, speaker2_start, speaker2_end

    model = Pipeline.from_pretrained(path_yaml)
    pipeline = model.instantiate(params)

    # send pipeline to GPU (when available)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    pipeline.to(torch.device(device))

    print("[info] Device:", device)
    logging.info(f"[info] Device: {device}")
    print("[info] Number of speakers:", num_speakers)
    logging.info(f"[info] Number of speakers: {num_speakers}")
    print("[info] Input file:", path_in)
    logging.info(f"[info] Input file: {path_in}")

    # preloading: Should be a bit faster (GPU: ~1 sec faster for full time of ~46s?)
    preloading_flag = True
    if preloading_flag:
        waveform, sample_rate = torchaudio.load(path_16)

    # Apply pretrained pipeline
    with ProgressHook() as hook:
        if preloading_flag:
            diarization = pipeline({"waveform": waveform, "sample_rate": sample_rate}, hook=hook, num_speakers=num_speakers)
        else:
            diarization = pipeline(path_16, hook=hook, num_speakers=num_speakers)

    print("Speaker diarization result:")
    logging.info("Speaker diarization result:")
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        print(f"\tstart={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")
        logging.info(f"\tstart={turn.start:.1f}s stop={turn.end:.1f}s speaker_{speaker}")
        speaker_id = speaker[-1]

        if (speaker_id == "0"):
            speaker1_start.append(float(f"{turn.start:.1f}"))
            speaker1_end.append(float(f"{turn.end:.1f}"))
        else:
            speaker2_start.append(float(f"{turn.start:.1f}"))
            speaker2_end.append(float(f"{turn.end:.1f}"))


if __name__ == "__main__":
    logging.basicConfig(filename=path_log, filemode="w", encoding='utf-8', level=logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)

    # Start time
    start_t = time.time()

    # Input arguments parser
    input_parser()

    # Parse configurations from config json file
    config_parser()

    # Prepare audio files with required sampling frequency of 16kh and 1 channel
    os.system(f"{path_ffmpeg} -i {path_in} -ar 16000 -ac 1 -y {path_16}")
    os.system(f"{path_ffmpeg} -i {path_in} -y {path_orig}")

    # Speaker Diarization
    speaker_diar()

    # Processing results
    logging.info("Before processing time cuts:")
    print("Before processing time cuts:")
    logging.info(f"\tspeaker1_start {speaker1_start}")
    print("\tspeaker1_start", speaker1_start)
    logging.info(f"\tspeaker1_end {speaker1_end}")
    print("\tspeaker1_end", speaker1_end)
    logging.info(f"\tspeaker2_start {speaker2_start}")
    print("\tspeaker2_start", speaker2_start)
    logging.info(f"\tspeaker2_end {speaker2_end}")
    print("\tspeaker2_end", speaker2_end)
    logging.info(f"\toverlap_start {overlap_start}")
    print("\toverlap_start", overlap_start)
    logging.info(f"\toverlap_end {overlap_end}")
    print("\toverlap_end", overlap_end)

    process_time_stamps()

    logging.info("After processing time cuts:")
    print("After processing time cuts:")
    logging.info(f"\tspeaker1_start {speaker1_start}")
    print("\tspeaker1_start", speaker1_start)
    logging.info(f"\tspeaker1_end {speaker1_end}")
    print("\tspeaker1_end", speaker1_end)
    logging.info(f"\tspeaker2_start {speaker2_start}")
    print("\tspeaker2_start", speaker2_start)
    logging.info(f"\tspeaker2_end {speaker2_end}")
    print("\tspeaker2_end", speaker2_end)
    logging.info(f"\toverlap_start {overlap_start}")
    print("\toverlap_start", overlap_start)
    logging.info(f"\toverlap_end {overlap_end}")
    print("\toverlap_end", overlap_end)

    create_audio_cuts()

    os.system(f"rm -f {path_orig}")
    os.system(f"rm -f {path_16}")

    end_t = time.time()
    print(f"[info] Total processing time: {(end_t-start_t)} sec ({(end_t-start_t)/60:.1f} min)")
    logging.info(f"[info] Total processing time: {(end_t-start_t)} sec ({(end_t-start_t)/60:.1f} min)")
