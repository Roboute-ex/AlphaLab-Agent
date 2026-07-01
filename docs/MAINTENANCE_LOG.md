# Maintenance Log

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
