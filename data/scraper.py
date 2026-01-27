import schedule
import time
import leaders
import stats


def job():
    leaders.scrape()
    stats.scrape()


schedule.every().day.at("00:00").do(job)
job()  # run at startup


if __name__ == "__main__":
    job()


while True:
    schedule.run_pending()
    time.sleep(1)
