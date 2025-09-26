import os
import subprocess
import argparse


NTHREADS = 0
DELETE = True
SUPPORTED_AUDIO_FORMATS = {"mp3", "wav"}
SUPPORTED_VIDEO_FORMATS = {
    "vid",
    "ts",
    "mov",
    "m4v",
    "mp4",
    "mkv",
    "webm",
    "mpg",
    "mpeg",
    "avi",
    "wmv",
    "flv",
}
VIDEO_PRESETS = {
    "COPY": {"ffpreset": "-c:a copy"},
    "H264": {"mark": "(AVC)", "ffpreset": "-c:v libx264"},
    "H265": {"mark": "(HEVC)", "ffpreset": "-c:v libx265"},
}
AUDIO_PRESETS = {
    # Copy audio codec
    "COPY": {"ffpreset": "-c:a copy"},
    # MP3 codec with default bitrate for all audio streams
    "MP3_ALL": {"ffpreset": "-c:a mp3"},
    # OPUS codec with 224kbps bitrate for all audio streams
    "LIBOPUS_ALL_224K": {"ffpreset": "-c:a libopus -ac 2 -b:a 224000"},
    # OPUS codec with 224kbps bitrate for the first audio stream - #0
    "LIBOPUS_0_224k": {"ffpreset": "-c:a:0 libopus -ac 2 -b:a 224000"},
    # OPUS codec with 224kbps bitrate for the second audio stream - #1
    "LIBOPUS_1_224k": {"ffpreset": "-c:a:1 libopus -ac 2 -b:a 224000"},
}


# Text Colors
class p_color:
    def red(txt):
        return f"\033[91m{txt}\033[00m"

    def green(txt):
        return f"\033[92m{txt}\033[00m"

    def yellow(txt):
        return f"\033[93m{txt}\033[00m"

    def blue(txt):
        return f"\033[94m{txt}\033[00m"

    def cyan(txt):
        return f"\033[96m{txt}\033[00m"

    def white(txt):
        return f"\033[97m{txt}\033[00m"


def parse_args():
    parser = argparse.ArgumentParser(p_color.white("Batch Media Converter"))

    parser.add_argument(
        "-i", "--input-dir", default=".", help='Input dir with files. (default: ".")'
    )
    parser.add_argument("-o", "--output-dir", help="Output dir")
    parser.add_argument(
        "-m",
        "--mode",
        choices={"ALL", "VIDEO", "AUDIO"},
        default="VIDEO",
        help="Type of files to search. ALL=VIDEO and AUDIO options merged, VIDEO=Just video files, AUDIO=Just audio files. (default: VIDEO)",
    )
    parser.add_argument(
        "-a",
        "--audio-preset",
        default="COPY",
        choices=AUDIO_PRESETS.keys(),
        help="Output audio preset. (default: COPY)",
    )
    parser.add_argument(
        "-v",
        "--video-preset",
        default="H265",
        choices=VIDEO_PRESETS.keys(),
        help="Output video preset. (default: H265)",
    )
    parser.add_argument("-n", "--input-format", default=None, nargs="*")
    parser.add_argument(
        "-f",
        "--output-format",
        default=None,
        help='Output file format for the files. (default: "mkv" for video input files, "mp3" for audio input files)',
    )
    parser.add_argument(
        "-p",
        "--preserve-files",
        default=False,
        action="store_true",
        help="Preserve input files.",
    )
    parser.add_argument(
        "-s",
        "--just_print",
        default=False,
        action="store_true",
        help="Just print the found files.",
    )
    parser.add_argument(
        "-l", "--limit", default=0, type=int, help="Limit count of files to convert."
    )

    params = parser.parse_args()

    return params


def get_input_formats(mode):
    if mode == "ALL":
        return SUPPORTED_VIDEO_FORMATS + SUPPORTED_AUDIO_FORMATS
    elif mode == "VIDEO":
        return SUPPORTED_VIDEO_FORMATS
    elif mode == "AUDIO":
        return SUPPORTED_AUDIO_FORMATS


def list_files(
    input_dir,
    output_dir,
    mode,
    audio_preset,
    video_preset,
    input_format=None,
    output_format=None,
    limit=0,
):
    batch = {}
    if input_format is None:
        input_format = get_input_formats(mode)

    for root, dirs, files in os.walk(input_dir, topdown=True):
        for name in files:

            mark = "."
            if any(name.lower().endswith(ext) for ext in SUPPORTED_VIDEO_FORMATS):
                mark = VIDEO_PRESETS[video_preset]["mark"]
                if output_format is None:
                    output_format = "mkv"
            elif (
                any(name.lower().endswith(ext) for ext in SUPPORTED_AUDIO_FORMATS)
                and output_format is None
            ):
                output_format = "mp3"

            if (
                any(name.lower().endswith(ext) for ext in input_format)
                and mark not in name
            ):
                in_file = os.path.join(root, name)

                ffpreset = " -map 0:v -map 0:a? -c copy {} {}".format(
                    VIDEO_PRESETS[video_preset]["ffpreset"],
                    (
                        AUDIO_PRESETS[audio_preset]["ffpreset"]
                        if audio_preset is not None
                        else ""
                    ),
                )

                out_file = os.path.join(
                    root, "{}.{}.{}".format(name.rsplit(".", 1)[0], mark, output_format)
                )
                if output_dir != input_dir:
                    out_file = out_file.replace(input_dir, output_dir)

                file = {
                    "out_file": out_file,
                    "ffpreset": ffpreset,
                    "size": os.path.getsize(in_file),
                }
                batch[in_file] = file
                if limit > 0 and len(batch.keys()) + 1 > limit:
                    return batch

    return batch


def bytes_to_human(nbytes: int):
    div = 1024
    labels = {0: "B", 1: "KB", 2: "MB", 3: "GB", 4: "TB"}
    lvl = 0
    while nbytes > div:
        nbytes = float(nbytes) / 1024
        lvl += 1

    return "{0:.2f} {1}".format(nbytes, labels[lvl])


def print_file(file, count=0, total=0):
    k = list(file.keys())[0]
    b = bytes_to_human(file[k]["size"])
    print(p_color.cyan(f'"{k}" - {b} - {count}/{total}'))


def print_filelist(filelist):
    tot_bytes = 0
    tot_files = len(filelist.keys())
    count = 1
    for k in sorted(filelist.keys()):
        print_file({k: filelist[k]}, count, tot_files)
        count += 1
        tot_bytes += filelist[k]["size"]
    return tot_bytes


def convert_filelist(filelist, preserve_files):
    tot_bytes_prev = 0
    tot_bytes_after = 0
    tot_files = len(filelist.keys())
    count = 1
    for k in sorted(filelist.keys()):
        print_file({k: filelist[k]}, count, tot_files)
        tot_bytes_prev += filelist[k]["size"]

        parent_dir = os.path.dirname(filelist[k]["out_file"])
        if not (os.path.exists(parent_dir) and os.path.isdir(parent_dir)):
            os.makedirs(parent_dir)

        command = (
            f'ffmpeg -i "{k}" {filelist[k]["ffpreset"]} "{filelist[k]["out_file"]}" -y'
        )
        print(p_color.yellow(command))

        try:
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
            process.wait()
            if process.returncode == 0:
                tot_bytes_after += os.path.getsize(filelist[k]["out_file"])
                if not preserve_files and os.path.exists(k):
                    print(p_color.blue(f'Delete "{k}"'))
                    os.remove(k)
        except KeyboardInterrupt:
            print(p_color.red("Keyboard Interrupt!"))
            return (
                count - 1,
                tot_files,
                tot_bytes_prev - filelist[k]["size"],
                tot_bytes_after,
            )

        count += 1

    return count - 1, tot_files, tot_bytes_prev, tot_bytes_after


def print_params(params):
    print(params)
    print(
        f'{p_color.white("Batch Media Converter")}\nInput Directory: "{params.input_dir}"\nOutput Directory: "{params.output_dir}"\nFile Type Mode: {params.mode}'
    )
    print(
        f'Audio Preset: {params.audio_preset} -> "{AUDIO_PRESETS[params.audio_preset]["ffpreset"]}"'
    )
    print(
        f'Video Preset: {params.video_preset} -> "{VIDEO_PRESETS[params.video_preset]["ffpreset"]}"'
    )
    print(
        f"Input Format:", "All" if params.input_format is None else params.input_format
    )
    print(
        f"Output Format:",
        (
            '"mkv" for video input files, "mp3" for audio input files'
            if params.output_format is None
            else params.output_format
        ),
    )
    print(f"Preserve Files: ", "No" if params.preserve_files == False else "Yes")
    print(f"Just Print: ", "No" if params.just_print == False else "Yes")
    print(f"Limit: ", "All" if params.limit == 0 else params.limit)


def main():
    params = parse_args()

    if params.output_dir == None:
        params.output_dir = params.input_dir

    print_params(params)

    print(p_color.white("Searching for files..."))
    filelist = list_files(
        params.input_dir,
        params.output_dir,
        params.mode,
        params.audio_preset,
        params.video_preset,
        params.input_format,
        params.output_format,
        params.limit,
    )
    print(p_color.green("OK!"))

    if params.just_print:
        tot_bytes = print_filelist(filelist)
        print(p_color.white(f"Total Bytes: {bytes_to_human(tot_bytes)}"))
    else:
        count, tot_files, tot_bytes_prev, tot_bytes_after = convert_filelist(
            filelist, params.preserve_files
        )
        print(
            p_color.white(
                f"Processed files: {count}/{tot_files}\nPrevious size: {bytes_to_human(tot_bytes_prev)}\nSize after processing: {bytes_to_human(tot_bytes_after)}"
            )
        )

    quit()


main()
