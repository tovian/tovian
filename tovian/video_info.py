# -*- coding: utf-8 -*-

"""
    Get information about video file
"""

import json
import subprocess


def video_info_ffmpeg(filename):
    """
    Return information about media file, using ffmpeg's tool "ffprobe"
    """
    try:
        p = subprocess.Popen(['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
    except OSError:
        return None

    try:
        data_ffmpeg = json.loads(out+err)
    except ValueError:
        return None

    return data_ffmpeg

def video_info(filename):
    """
    Extract useful information about media file
    """
    data_ffmpeg = video_info_ffmpeg(filename)
    data_out = {}

    try:
        data_out['duration'] = float(data_ffmpeg['format']['duration'])
    except:
        pass

    try:
        for data_stream in data_ffmpeg['streams']:
            if data_stream['codec_type']=='video':
                try:
                    data_out['width'] = int(data_stream['width'])
                except:
                    pass

                try:
                    data_out['height'] = int(data_stream['height'])
                except:
                    pass

                try:
                    data_out['frames'] = int(data_stream['nb_frames'])
                except:
                    pass

                try:
                    # safely evaluate e.g. "24000/1001"
                    ns = {'__builtins__': None}
                    data_out['fps'] = eval(data_stream['r_frame_rate']+'.0', ns)
                except:
                    pass
    except:
        pass

    return data_out