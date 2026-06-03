# JD Collector

定期抓取 JD，结构化后存入 `data/jd_raw/`，并自动推送到仓库。

## 目录结构

```
jd_collector/
├── config.py          # 数据源配置（关键字、岗位类型、来源）
├── fetcher.py         # 多源 JD 抓取（手动/Apify/RSS）
├── parser.py          # JD 文本 → 结构化 JSON
├── dedup.py           # 去重（基于 JD 文本 hash）
├── sync_to_github.py  # 把新增 JD 推送到 GitHub
└── scheduler.py       # 定期触发（每天 09:00 HKT）
```

## 快速开始

```bash
pip install -r requirements.txt
export GITHUB_TOKEN=your_token
export APIFY_TOKEN=your_token  # 可选，手动粘贴时不需要

# 单次运行
python -m job_agent.jd_collector.scheduler --once

# 后台定时
python -m job_agent.jd_collector.scheduler
```

## 数据源优先级

1. **手动粘贴**：运行 `python -m job_agent.jd_collector.fetcher --manual`，粘贴 JD 文本后回车两次
2. **Apify**：配置 `APIFY_TOKEN` 后自动批量拉取 LinkedIn JD
3. **RSS/公开聚合**：应届生、实习僧等网站公开 JD（合规）
