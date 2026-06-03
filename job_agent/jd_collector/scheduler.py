"""定时调度：每天 09:00 HKT 采集 → 解析 → 去重 → 推送 GitHub"""
import argparse
import time
from datetime import datetime

import schedule
import pytz

from .config import DATA_DIR, SCHEDULE
from .dedup import remove_duplicates
from .fetcher import fetch_all, fetch_manual
from .parser import parse_all_pending
from .sync_to_github import sync_all


def run_pipeline(manual: bool = False) -> None:
    """完整 JD 采集管道"""
    print(f"\n{'='*50}")
    print(f"[scheduler] 开始采集 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 采集
    if manual:
        fetch_manual()
    else:
        fetch_all()

    # 2. 解析结构化字段
    parse_all_pending(DATA_DIR)

    # 3. 去重
    remove_duplicates(DATA_DIR)

    # 4. 推送 GitHub
    sync_all(DATA_DIR)

    print(f"[scheduler] 管道完成 {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*50}\n")


def main():
    parser = argparse.ArgumentParser(description="JD 采集调度器")
    parser.add_argument("--once", action="store_true", help="立即运行一次后退出")
    parser.add_argument("--manual", action="store_true", help="手动粘贴 JD 模式")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不实际推送")
    args = parser.parse_args()

    if args.once or args.manual:
        run_pipeline(manual=args.manual)
        return

    # 定时模式
    tz = pytz.timezone(SCHEDULE["timezone"])
    run_time = f"{SCHEDULE['hour']:02d}:{SCHEDULE['minute']:02d}"
    print(f"[scheduler] 定时模式启动，每天 {run_time} {SCHEDULE['timezone']} 执行")

    schedule.every().day.at(run_time).do(run_pipeline)

    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()
