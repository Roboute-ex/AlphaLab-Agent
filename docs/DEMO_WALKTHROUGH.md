# Demo Walkthrough

## 1. Purpose

这个 walkthrough 帮助新读者快速理解 AlphaLab Agent 的设计，并在本地复现实验流程。它不是固定演讲稿，而是一个项目演示路线。

## 2. Minimal local run

1. 阅读 README 的项目定位，确认本项目是 deterministic local research workflow，不是金融聊天机器人或实盘交易系统。
2. 运行版本命令：

   ```powershell
   py -m alphalab_agent.cli --version
   ```

3. 运行默认 demo：

   ```powershell
   py -m alphalab_agent.cli --demo
   ```

4. 打开 `artifacts/report.md`，查看 research summary、risk metrics、Reviewer findings。
5. 打开 `artifacts/run_manifest.json`，查看 config、metrics、reviewer checks 和 artifact paths。
6. 解释 Reviewer `WARN` 为什么不是失败：`WARN` 表示研究质量有保守提示，而不是 pipeline broken。
7. 运行 agent-demo：

   ```powershell
   py -m alphalab_agent.cli --agent-demo --goal "研究默认 synthetic 多因子策略"
   ```

8. 总结 Agent 和普通 backtest script 的区别：Agent 负责 planning、step logs、Reviewer、manifest、report；普通脚本通常只输出一次策略收益。

## 3. Extended run

可以继续展示：

- data quality: 查看 `## Data Quality`。
- execution backtest: 说明默认不直接用 forward return label 当主收益。
- benchmark: 比较 equal-weight、random top-k、single-factor baseline。
- walk-forward: 查看样本外验证。
- supervised model: 运行 `py -m alphalab_agent.cli --demo --enable-supervised-model`。
- manifest: 用 `run_manifest.json` 复核配置和结果。
- CI/tests: 运行 `py -m pytest -q` 和 `py scripts\run_tests.py`。

## 4. Common design questions

### 这和金融聊天机器人有什么区别？

金融聊天机器人通常回答自然语言问题。AlphaLab Agent 是 deterministic research workflow agent，核心结果来自 Python 代码，而不是 LLM 生成。

### 为什么不用真实交易？

本项目目标是研究流程复现，不是实盘交易。接入券商、下单和交易风控会改变项目边界，并引入不必要风险。

### 为什么默认 synthetic data？

synthetic data 让测试、demo 和 CI 可以 offline-safe、deterministic、reproducible。CSV / yfinance 仍可显式启用，但不是默认路径。

### 如何避免未来函数？

默认 backtest 使用 execution-based signal-to-portfolio 逻辑，信号日的 score 只作用于后续 realized return。forward return label 用于 IC / RankIC 和诊断，而不是默认主回测收益来源。

### 为什么 Reviewer 是 WARN？

Reviewer `WARN` 表示策略或因子质量有保守提示，例如 benchmark、drawdown、turnover、成本或样本外表现仍需谨慎。它不是 pipeline 失败。

### supervised model 如何避免 leakage？

监督模型在 walk-forward 中只用 train window 拟合，在 test window 预测；时间序列不随机切分，不使用 test label 训练。

### v0.10 为什么不是继续堆模型？

v0.10 的目标是让 Agent 设计更透明、README 更完整、demo 更容易复现，并沉淀项目设计文档。这比继续增加模型更符合当前项目成熟度。
