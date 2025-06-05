from datetime import datetime, timedelta
from collections import Counter
import csv
import sys
import os
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Load environment variables
load_dotenv()

# 設定
CSV_PATH = "awb_sample.csv"
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
SLACK_CHANNEL = "#tous-python-labo"
client = WebClient(token=SLACK_TOKEN)

def load_csv_rows():
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)

def send_to_slack(message):
    try:
        client.chat_postMessage(channel=SLACK_CHANNEL, text=message)
    except SlackApiError as e:
        print(f"❌ Slack API エラー: {e.response['error']}")

def save_to_txt(message, filename="daily_report.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(message)
    print(f"📄 {filename} に出力完了。")

def show_specific_day(target_date):
    try:
        date_obj = datetime.now().date() if target_date == "today" else datetime.strptime(target_date, "%Y-%m-%d").date()
    except ValueError:
        print("❌ 日付形式が正しくありません。例: 2025-06-05 または today")
        return

    rows = load_csv_rows()
    filtered = [
        f":camion: {row['AWB番号']} | 荷主: {row['荷主']}"
        for row in rows
        if datetime.strptime(row["ETA"], "%Y-%m-%d").date() == date_obj
    ]

    date_str = date_obj.strftime("%Y年%m月%d日")
    if filtered:
        message = f":package: [{target_date}] {date_str} の到着予定：\n" + "\n".join(filtered)
    else:
        message = f":package: [{target_date}] {date_str} の到着予定：\n（なし）"

    print(message)
    send_to_slack(message)
    save_to_txt(message)

def show_weekly():
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    week_dates = [monday + timedelta(days=i) for i in range(7)]

    rows = load_csv_rows()
    filtered = [row for row in rows if datetime.strptime(row["ETA"], "%Y-%m-%d").date() in week_dates]
    counts = Counter(row["荷主"] for row in filtered)

    report = ":calendar: 今週の荷物集計（会社別）:\n"
    for k, v in counts.items():
        report += f"- {k}: {v}件\n"

    for d in week_dates:
        daily = [
            f":camion: {row['AWB番号']} | 荷主: {row['荷主']}"
            for row in filtered
            if datetime.strptime(row["ETA"], "%Y-%m-%d").date() == d
        ]
        report += f"\n📦 {d.strftime('%Y年%m月%d日')}（{d.strftime('%a')}）: {len(daily)}件\n"
        if daily:
            report += "\n".join(daily) + "\n"

    print(report)
    send_to_slack(report)
    save_to_txt(report)

# 実行
if __name__ == "__main__":
    if len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg == "today" or "-" in arg:
            show_specific_day(arg)
        elif arg == "weekly":
            show_weekly()
        else:
            print("❌ 不正な引数です。today / YYYY-MM-DD / weekly のいずれかを指定してください。")
    else:
        print("❌ 引数が必要です。today / YYYY-MM-DD / weekly を指定してください。")
