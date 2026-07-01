# Release Checklist

适用于 AlphaLab Agent 的轻量发布检查。不要把它变成复杂企业流程，目标是减少个人项目发布失误。

## Release 前检查

- 确认当前分支包含目标版本改动。
- 确认 README、PROJECT_PLAN、CHANGELOG、版本号一致。
- 确认没有接入 LLM、实盘交易、自动下单或默认联网。
- 确认没有提交真实 API key 或敏感数据。

## 本地测试命令

```powershell
py -m pytest -q
py scripts\run_tests.py
py -m alphalab_agent.cli --version
py -m alphalab_agent.cli --demo
py -m alphalab_agent.cli --demo --data-source csv --csv-path examples/sample_ohlcv.csv
py -m alphalab_agent.cli --demo --enable-supervised-model
```

## Git 状态检查

```powershell
git status
```

确认 artifacts 生成物没有进入 staged files。

## Branch / Merge / Tag / Push

1. 在 feature branch 完成测试。
2. 合并到 `main` 前确认 CI 通过。
3. 合并后在 `main` 上确认版本号。
4. 创建 tag，例如 `v0.9`。
5. push branch 和 tag。

## GitHub Actions 检查

- 确认 CI green check。
- Node.js deprecation warning 不等于 Python 测试失败。
- 如果 CI 失败，先看失败命令和 traceback，不要盲目改依赖或 action 大版本。

## GitHub Release 创建检查

- Release title 使用版本号。
- Release notes 可从 CHANGELOG 摘取，不要夸大未实现功能。
- 风险提示保留：不是投资建议、不接实盘、不下单。

## Tag 打错时

安全步骤：

1. 先确认错误 tag 指向。
2. 不要用 `git reset --hard` 清理历史。
3. 如需重打 tag，先删除本地错误 tag，再删除远端错误 tag。
4. 重新在正确 commit 上创建 tag。
5. push 新 tag 后再次检查 GitHub Actions 和 release 页面。

## CI 失败时

- 先复现失败命令。
- 如果是依赖遗漏，补 `pyproject.toml` 并加测试或说明。
- 如果是测试本身不稳定，优先修 deterministic 输入，不要降低 Reviewer 规则来美化结果。
- 如果是 GitHub warning，确认是否真正导致 job failure。
