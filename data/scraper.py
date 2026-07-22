import schedule
import time
from pathlib import Path
import leaders
import stats


def remove_root_png_files():
    for png_file in Path("/app/").glob("*.png"):
        try:
            png_file.unlink()
        except OSError:
            pass


def job():
    remove_root_png_files()
    leaders.scrape()
    stats.scrape()


schedule.every().day.at("00:00").do(job)
job()  # run at startup


if __name__ == "__main__":
    job()


while True:
    schedule.run_pending()
    time.sleep(1)
