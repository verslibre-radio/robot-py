import shutil
import os
import argparse
import pandas as pd
import gspread

from datetime import datetime
from loguru import logger
from pydub import AudioSegment
from pydub.silence import detect_leading_silence
from pathlib import Path
from pydub import AudioSegment
from mixing.utils import get_filename, get_metadata, add_metadata_to_mp3

SHEET_ID="1j2w0MPDL0R9Z_9XE5G_luDo4PgPEWhf6RNhwbxh7lmw"
SHEET_NAME="meta"                                                                                                                                  

def trim_sound(src_audio_path, src_audio_filename, dst_audio_path, dst_audio_filename) -> str:  
    dst_path = Path(dst_audio_path) / Path(dst_audio_filename)
    src_path = Path(src_audio_path) / Path(src_audio_filename)
    try:
        trim_leading_silence: AudioSegment = lambda x: x[detect_leading_silence(x) :]
        trim_trailing_silence: AudioSegment = lambda x: trim_leading_silence(x.reverse()).reverse()
        strip_silence: AudioSegment = lambda x: trim_trailing_silence(trim_leading_silence(x))
        sound = AudioSegment.from_file(src_path)
        stripped = strip_silence(sound)
        out = stripped.fade_in(3000).fade_out(3000)
        out.export(dst_path, format="mp3", bitrate="320k")
    except Exception as e:
        logger.info(f"FAILED: Trim and fade in/out for: {src_audio_filename}")
        logger.error(e)
        shutil.copyfile(src_path, dst_path)
    else:
        logger.info(f"PASSED: Trim and fade in/out for: {src_audio_filename}")

    os.remove(src_path)

    return str(dst_path)

def trimming(df: pd.DataFrame, src_audio_path: str, dst_audio_path: str) -> None:
    source_file_list = [f for f in os.listdir(src_audio_path) if not f.startswith('.')]
    if len(source_file_list) == 0:
        logger.info(f"No files to trim, exiting")
    else:
        for file_name in source_file_list:
            logger.info(f"Starting trimming sound for {file_name}")

            tag = file_name.split('-',2)[1]
            date = file_name.split(' ',2)[0]

            df_active=df[df["tag"]==tag]
            show_name, dj_name, ep_nr, genre = get_metadata(df_active)
            dst_audio_filename = get_filename(tag, show_name, dj_name, ep_nr, date)

            dst_path = trim_sound(src_audio_path, file_name, dst_audio_path, dst_audio_filename)

            date_rec = datetime.strptime(dst_audio_filename.split('_',2)[0], '%Y%m%d')
            add_metadata_to_mp3(dst_path, show_name, dj_name, ep_nr, genre, date_rec.year)

        logger.info("Finished trimming stage")

def get_sheet(cred_path: str) -> pd.DataFrame:
    gc = gspread.service_account(filename=cred_path)
    spreadsheet = gc.open_by_key(SHEET_ID)
    worksheet = spreadsheet.worksheet(SHEET_NAME)
    rows = worksheet.get_all_records()
    df = pd.DataFrame.from_dict(rows)

    return df

def main():
    parser = argparse.ArgumentParser(description='Program to trim dead audio and add fades')
    parser.add_argument(
        '--path',
        default = "/var/lib/robot",
        help = "Path to local root folder used for storing audio"
    )
    parser.add_argument(
        '--credentials',
        default = "/etc/robot/cred.json",
        help = "Path to credentials file"
    )

    args = parser.parse_args()
    df = get_sheet(args.credentials)
    src_audio_path = Path(args.path) / "to_mix" 
    dst_audio_path = Path(args.path) / "to_upload" 
    dst_audio_path.mkdir(parents=True, exist_ok=True)

    trimming(df, str(src_audio_path), str(dst_audio_path))

if __name__ == "__main__":
    main()
