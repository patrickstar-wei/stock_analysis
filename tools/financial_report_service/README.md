# A股财报自动获取服务

基于 FastAPI 的批量财报抓取服务：
- 输入：CSV（必填列 `code`，可选 `name`）
- 抓取：巨潮资讯年报/中报/一季报/三季报 PDF
- 提取：固定核心财务指标（PDF 优先，AkShare 回退）
- 输出：`PDF + reports_manifest.json + financial_metrics.csv + errors.jsonl + job_summary.json`

## 目录

```text
tools/financial_report_service/
├── app/
├── output/
├── state/
├── tests/
├── environment.yml
├── start_with_conda.sh
└── requirements.txt
```

## 一键创建环境并启动（Conda）

```bash
cd tools/financial_report_service
chmod +x start_with_conda.sh
./start_with_conda.sh
```

默认行为：
- 环境名：`financial_report_service`
- 监听地址：`0.0.0.0:8000`
- 自动热重载：开启

可选环境变量：

```bash
ENV_NAME=my_report_env PORT=9000 RELOAD=false ./start_with_conda.sh
```

## 手动 Conda 方式

```bash
cd tools/financial_report_service
conda env create -f environment.yml
conda activate financial_report_service
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问：
- Swagger: `http://localhost:8000/docs`
- 健康检查: `GET http://localhost:8000/api/v1/healthz`

如果浏览器“没反应”，先检查：

```bash
curl http://127.0.0.1:8000/api/v1/healthz
```

- 若报端口占用：`lsof -i :8000` 后停止占用进程，或改端口启动：`PORT=9000 ./start_with_conda.sh`
- 若你在远程机器/容器里运行，需要在 IDE 做端口转发后访问转发地址

## API

### 1) 提交任务

`POST /api/v1/jobs` (multipart/form-data)
- `file`: CSV 文件（必填）
- `years`: 回溯年限，默认 `3`
- `full_refresh`: 是否全量，默认 `false`
- `report_types`: 逗号分隔，默认 `annual,semi,q1,q3`

示例：

```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -F "file=@./sample_codes.csv" \
  -F "years=3" \
  -F "full_refresh=false" \
  -F "report_types=annual,semi,q1,q3"
```

返回：

```json
{"job_id":"...","status":"queued","created_at":"..."}
```

### 2) 查询任务状态

`GET /api/v1/jobs/{job_id}`

### 3) 查询任务结果路径

`GET /api/v1/jobs/{job_id}/results`

## CSV格式

```csv
code,name
000001,平安银行
600519,贵州茅台
300750,宁德时代
```

## 输出产物

每个任务在：`output/{job_id}/`
- `pdf/{code}/{announcement_id}.pdf`
- `reports_manifest.json`
- `financial_metrics.csv`
- `errors.jsonl`
- `job_summary.json`

全局增量索引：`state/report_index.json`

## 扫描版PDF策略

若 PDF 文本长度过短且关键指标提取不足，会判定为扫描版：
- 保留已下载 PDF
- 记录错误与状态 `scanned_skipped`
- 不中断任务

## 测试

```bash
cd tools/financial_report_service
PYTHONPATH=. pytest -q
```
