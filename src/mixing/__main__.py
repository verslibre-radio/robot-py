import argparse
import os
import shutil
from pathlib import Path

import gspread
import pandas as pd
from loguru import logger
from pydub import AudioSegment
from pydub.silence import detect_leading_silence

from mixing.utils import get_filename, get_metadata

SHEET_ID = "1j2w0MPDL0R9Z_9XE5G_luDo4PgPEWhf6RNhwbxh7lmw"
SHEET_NAME = "meta"


def trim_sound(
    src_audio_path: str,
    src_audio_filename: str,
    dst_audio_path: str,
    dst_audio_filename: str,
) -> str:
    dst_path = Path(dst_audio_path) / Path(dst_audio_filename)
    src_path = Path(src_audio_path) / Path(src_audio_filename)
    try:
        trim_leading_silence: AudioSegment = lambda x: x[detect_leading_silence(x) :]
        trim_trailing_silence: AudioSegment = lambda x: trim_leading_silence(
            x.reverse(),
        ).reverse()
        strip_silence: AudioSegment = lambda x: trim_trailing_silence(
            trim_leading_silence(x),
        )
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

    src_path.unlink()


def trimming(df: pd.DataFrame, src_audio_path: str, dst_audio_path: str) -> None:
    source_file_list = [f for f in os.listdir(src_audio_path) if not f.startswith(".")]
    if len(source_file_list) == 0:
        logger.info("No files to trim, exiting")
    else:
        for file_name in source_file_list:
            logger.info(f"Starting trimming sound for {file_name}")

            tag = file_name.split("-", 2)[1]
            date = file_name.split(" ", 2)[0]

            df_active = df[df["tag"] == tag]
            show_name, dj_name, ep_nr, genre = get_metadata(df_active)
            dst_audio_filename = get_filename(tag, show_name, dj_name, ep_nr, date)

            trim_sound(src_audio_path, file_name, dst_audio_path, dst_audio_filename)

        logger.info("Finished trimming stage")


def get_sheet(cred_path: str) -> pd.DataFrame:
    gc = gspread.service_account(filename=cred_path)
    spreadsheet = gc.open_by_key(SHEET_ID)
    worksheet = spreadsheet.worksheet(SHEET_NAME)
    rows = worksheet.get_all_records()

    return pd.DataFrame.from_dict(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Program to trim dead audio and add fades"
    )
    parser.add_argument(
        "--path",
        default="/var/lib/robot",
        help="Path to local root folder used for storing audio",
    )
    parser.add_argument(
        "--credentials", default="/etc/robot/cred.json", help="Path to credentials file"
    )

    args = parser.parse_args()
    df_data = get_sheet(args.credentials)
    src_audio_path = Path(args.path) / "to_mix"
    dst_audio_path = Path(args.path) / "to_upload"
    dst_audio_path.mkdir(parents=True, exist_ok=True)

    trimming(df_data, str(src_audio_path), str(dst_audio_path))


if __name__ == "__main__":
    main()
