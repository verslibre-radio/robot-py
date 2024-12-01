import argparse
import os
import shutil
import sqlite3
from pathlib import Path

from loguru import logger
from pydub import AudioSegment
from pydub.silence import detect_leading_silence


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


def trimming(cursor: sqlite3.Cursor, src_audio_path: str, dst_audio_path: str) -> None:
    source_file_list = [f for f in os.listdir(src_audio_path) if not f.startswith(".")]
    if len(source_file_list) == 0:
        logger.info("No files to trim, exiting")
    else:
        for file_name in source_file_list:
            logger.info(f"Starting trimming sound for {file_name}")

            file_name_tokens = file_name.split("_", 2)
            date = file_name_tokens[0]
            tag = file_name_tokens[1].split(".")[0]

            rows = cursor.execute(
                "SELECT * FROM base_data where TAG = ?", (tag,)
            ).fetchall()
            show_data = rows[0]

            dst_audio_filename = get_filename(
                tag, show_data[1], show_data[3], show_data[2], date
            )

            trim_sound(src_audio_path, file_name, dst_audio_path, dst_audio_filename)

        logger.info("Finished trimming stage")


def get_filename(tag: str, show_name: str, dj_name: str, ep_nr: str, date: str) -> str:
    filename = f"{date}_{tag}_{show_name}_{ep_nr}_{dj_name}.mp3"
    return filename.replace(" ", "_").replace("/", "").replace("&","and")


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
    base_path = Path(args.path)
    src_audio_path = base_path / "to_mix"
    dst_audio_path = base_path / "to_upload"
    sql_path = base_path / "metadata.sql"
    dst_audio_path.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(sql_path)
    cursor = conn.cursor()

    trimming(cursor, str(src_audio_path), str(dst_audio_path))


if __name__ == "__main__":
    main()
