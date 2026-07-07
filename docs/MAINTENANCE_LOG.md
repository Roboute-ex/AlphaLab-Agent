# Maintenance Log

## v0.10 maintenance log

本轮做 v0.10，是为了让 Agent 设计更透明，让 README 更容易理解，让 demo 流程更容易复现，并沉淀项目设计记录。

因为 v0.10 尚未 push、tag 或 release，本轮把 maintenance hygiene 内容合并进同一个 v0.10，而不是新增后续版本。合并后的版本名是 `v0.10 - Agent Design Transparency and Maintenance Hygiene`。

维护动机：

- 展示持续维护，而不是只保留一次性 demo。
- 减少 “Agent” 概念误解：这里的 Agent 是 deterministic research workflow agent，不是金融聊天机器人。
- 增强 README 可读性，让新读者能理解 PlannerAgent、ResearchPlan、Reviewer、report 和 manifest 的关系。
- 增强 demo reproducibility，补充 demo walkthrough。
- 沉淀 project notes，记录技术设计、Agent 设计和后续轻量方向。
- 补充 runbook，记录标准验证命令、预期输出、release routine 和 when not to release。
- 补充 troubleshooting guide，覆盖 pytest import、Streamlit fallback、yfinance optional、Reviewer WARN、CI、version mismatch 和 generated artifacts。
- 补充 config guide 和示例 JSON，帮助读者理解 synthetic / CSV / supervised model / output config。
- 补充 artifact hygiene 和 documentation maintenance tests，避免生成物误提交和文档入口漂移。

保留安全边界：

- 默认 synthetic data。
- 不接 OpenAI API，不接 LLM。
- 不接实盘交易，不自动下单。
- 不默认联网。
- 不保存 API key。
- 不让 LLM 生成收益、风险、Reviewer 或回测结果。

## v0.9 maintenance update

本轮选择做维护版，是为了展示 AlphaLab Agent 不是一次性 demo，而是持续维护的研究项目。

治理改进：

- 新增 `CHANGELOG.md`，记录版本演进和安全边界。
- 新增维护说明和 release checklist，降低发布失误风险。
- 新增版本一致性测试，避免 pyproject、package version、README、PROJECT_PLAN、CLI 输出互相漂移。
- 新增 README command smoke tests，防止核心命令过期。
- 新增 manifest schema stability tests，保护 `run_manifest.json` 的可复现字段。
- 新增 issue / PR templates，提醒贡献者不要上传真实 API key 或敏感数据。
- 改进 CI hygiene：pip cache 和 CLI version check。

保留安全边界：

- 默认 synthetic data。
- 不接 OpenAI API，不接 LLM。
- 不接实盘交易，不自动下单。
- 不默认联网。
- 不保存 API key。
- 不新增重依赖或强化学习交易 Agent。
