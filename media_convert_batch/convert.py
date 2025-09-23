import os
import subprocess
import argparse


NTHREADS=0
DELETE=True
SUPPORTED_AUDIO_FORMATS={'mp3', 'wav'}
SUPPORTED_VIDEO_FORMATS={'vid', 'ts', 'mov', 'm4v', 'mp4', 'mkv', 'webm', 'mpg', 'mpeg', 'avi', 'wmv', 'flv'}
VIDEO_PRESETS={
    "COPY": {
        "ffpreset": "-c:a copy"
    },
    "H264": {
        "mark": "(AVC)",
        "ffpreset": "-c:v libx264"
    },
    "H265": {
        "mark": "(HEVC)",
        "ffpreset": "-c:v libx265"
    }
}
AUDIO_PRESETS={
    # Copy audio codec
    "COPY": {
        "ffpreset": "-c:a copy"
    },
    # MP3 codec with default bitrate for all audio streams
    "MP3_ALL": {
        "ffpreset": "-c:a mp3"
    },
    # OPUS codec with 224kbps bitrate for all audio streams
    "LIBOPUS_ALL_224K": {
        "ffpreset": "-c:a libopus -ac 2 -b:a 224000"
    },
    # OPUS codec with 224kbps bitrate for the first audio stream - #0
    "LIBOPUS_0_224k": {
        "ffpreset": "-c:a:0 libopus -ac 2 -b:a 224000"
    },
    # OPUS codec with 224kbps bitrate for the second audio stream - #1
    "LIBOPUS_1_224k": {
        "ffpreset": "-c:a:1 libopus -ac 2 -b:a 224000"
    }
}


# Text Colors
class p_color():
    def red(txt): return f'\033[91m{txt}\033[00m'
    def green(txt): return f'\033[92m{txt}\033[00m'
    def yellow(txt): return f'\033[93m{txt}\033[00m'
    def blue(txt): return f'\033[94m{txt}\033[00m'
    def cyan(txt): return f'\033[96m{txt}\033[00m'
    def white(txt): return f'\033[97m{txt}\033[00m'


def parse_args():
    parser = argparse.ArgumentParser(p_color.white('Batch Media Converter'))
    
    parser.add_argument('-i', '--input-dir', default='.', help='Input dir with files. (default: ".")')
    parser.add_argument('-o', '--output-dir', help='Output dir')
    parser.add_argument('-m', '--mode', choices={'ALL', 'VIDEO', 'AUDIO'}, default='VIDEO', help='Type of files to search. ALL=VIDEO and AUDIO options merged, VIDEO=Just video files, AUDIO=Just audio files. (default: VIDEO)')
    parser.add_argument('-a', '--audio-preset', default='COPY', choices=AUDIO_PRESETS.keys(), help='Output audio preset. (default: COPY)')
    parser.add_argument('-v', '--video-preset', default='H265', choices=VIDEO_PRESETS.keys(), help='Output video preset. (default: H265)')    
    parser.add_argument('-n', '--input-format', default=None, nargs='*')
    parser.add_argument('-f', '--output-format', default=None, help='Output file format for the files. (default: "mkv" for video input files, "mp3" for audio input files)')
    parser.add_argument('-p', '--preserve-files', default=False, action='store_true', help='Preserve input files.')
    parser.add_argument('-s', '--just_print', default=False, action='store_true', help="Just print the found files.")
    parser.add_argument('-l', '--limit', default=0, type=int, help="Limit count of files to convert.")
    
    params = parser.parse_args()

    return params


def main():
    print(parse_args())
    quit()


main()
