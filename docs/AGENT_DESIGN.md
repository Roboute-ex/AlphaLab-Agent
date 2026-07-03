# AlphaLab Agent Design

## 1. Why a deterministic agent?

AlphaLab Agent 采用 deterministic agent，是因为量化研究需要可复现、可审计、可测试。

不用 LLM 直接给研究结论的原因：

- 量化研究的收益、风险、回撤、成本和 Reviewer 结论必须能被复验。
- LLM 容易幻觉，不适合直接生成收益 / 风险指标。
- deterministic agent 更适合严肃的 research workflow。
- deterministic design 让项目更容易维护、测试和复盘。

这里的 Agent 不是替代研究判断，而是把研究流程拆成明确步骤并稳定执行。

## 2. Agent roles

- `PlannerAgent`: 把用户研究目标转成结构化 `ResearchPlan`。
- `Research Pipeline`: 执行数据、因子、标签、回测、benchmark、walk-forward、ML OOS、sensitivity。
- `Reviewer Agent`: 检查研究有效性和风险，包括 benchmark、drawdown、turnover、cost drag、IC stability、data quality。
- `Report / Manifest`: 输出 `report.md`、`report.html`、`run_manifest.json`，让结果可复现、可审计。

## 3. What the agent does

- plans the research workflow。
- records step logs。
- runs deterministic modules。
- checks data quality。
- compares benchmarks。
- reviews robustness。
- exports reproducible artifacts。

## 4. What the agent does not do

- no financial advice。
- no live trading。
- no broker API。
- no auto order execution。
- no API key storage。
- no default network access。
- no LLM-generated return/risk/reviewer results。

## 5. Anti-hallucination design

AlphaLab Agent 的 anti-hallucination 设计依赖工程边界，而不是提示词承诺：

- 数值结果来自 deterministic Python functions。
- tests protect expected behavior。
- manifest records configuration and outputs。
- Reviewer uses rule-based checks。
- reports expose assumptions and limitations。

即使未来加入更丰富的 agent wrapper，收益、风险、Reviewer 和回测结果仍应由确定性代码生成。

## 6. Reproducibility design

- fixed seed synthetic data。
- explicit config。
- `run_manifest.json`。
- pytest and fallback runner。
- README command smoke tests。
- manifest schema tests。

这些设计让一个本地实验可以被重新运行、检查和比较，而不是只停留在一次性 demo 输出。

## 7. Why this matters

这个项目的价值不在于预测未来收益，而在于把量化研究流程拆成可解释、可复现、可测试的 workflow。Agent 的意义是让研究过程更结构化，而不是替代研究判断。
