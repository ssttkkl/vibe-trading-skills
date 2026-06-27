# Vibe-Trading Swarm Architecture

## 核心架构

vibe-trading 的 swarm 不是 LangChain Chain，也不是纯自编排 agent。它是**显式 DAG 编排 + 每个节点独立 ReAct 循环**。

### 编排层 (runtime.py)

```
1. build_run_from_preset() → 从 YAML 构建 SwarmRun (agents + tasks)
2. validate_dag(tasks) → 验证 DAG 无循环
3. topological_layers(tasks) → 拓扑排序生成执行层
4. 按层序串行执行，每层内 ThreadPoolExecutor 并行
5. 每层完成后 collect task_summaries
6. 用 input_from 映射替换下游 system_prompt 的 {upstream_context}
7. 启动下一层 workers
```

### 数据流

```yaml
tasks:
  - id: task-macro            # Layer 0
    depends_on: []
    
  - id: task-technical         # Layer 1
    depends_on: [task-macro]   # 明确依赖
    input_from:                # 显式数据映射
      macro_context: task-macro
```

`task-macro` 完成后，runtime 收集其 `summary` → 存入 `task_summaries["task-macro"]` → 在 Layer 1 的 system_prompt 中将 `{upstream_context}` 替换为 `### macro_context\n[summary内容]`。

### Worker 层 (worker.py)

每个 task = 一个独立 worker = 一个 ReAct 循环：

```
for iteration in range(max_iterations):   # 默认 50
    response = llm.stream_chat(messages, tools=registry.get_definitions())
    if response.has_tool_calls:
        → 执行 tool → 结果放回 messages → 继续循环
    else:
        → 这是最终输出 → 写入 report.md
```

Worker 构建过程：

1. `build_swarm_registry(tools_whitelist)` → 从 YAML 的 `tools` 字段过滤可用 tool
2. `SkillsLoader()` → 加载 `src/skills/` 下所有技能
3. `_filter_skill_descriptions(loader, agent_spec.skills)` → 只保留 whitelist 技能
4. `build_worker_prompt()` → system_prompt = role + upstream_context + skill_desc + grounding + data_citation + execution_rules
5. `run_worker()` → 启动 ReAct 循环

### 73 个技能的真实位置

不在 github 仓库里（用户找不到是因为），它们在 pipx venv 的安装包：

```
~/.local/pipx/venvs/vibe-trading-ai/lib/python3.14/site-packages/src/skills/<name>/SKILL.md
```

**技能不是插件/代码**——它们是方法论文档（Markdown）。LLM 用 `load_skill('technical-basic')` 读取文档 → 学习分析框架 → 用工具的 `read_url`/`get_market_data` 获取实时数据 → 应用框架产出分析。

## 与 Session 模式的区别

| | Session (POST /messages) | Swarm Preset |
|---|---|---|
| **编排** | 单 agent ReAct 循环 | 多 agent DAG，层内并行 |
| **数据流** | 全部在 context 窗口内 | 层间通过 `input_from` 传递 |
| **load_skill** | 能用但 token 开销大 | ✅ 每个 worker 有独立的 skills whitelist |
| **可靠性** | 长 context 易溢出/token limit | 每个 worker context 隔离，互不影响 |
| **适用** | 简单的单轮分析 | 复杂的多维度多标的分析 |

## 自定义 Preset 生命周期

预设 YAML 存在 `src/swarm/presets/<name>.yaml`（在 pipx venv 内）。

**升级 vibe-trading 后会被覆盖。** 备份到 `~/.hermes/swarm-presets/`。

恢复：
```bash
cp ~/.hermes/swarm-presets/<name>.yaml \
  ~/.local/pipx/venvs/vibe-trading-ai/lib/python3.14/site-packages/src/swarm/presets/
```

## 现有 preset 结构参考

29 个内置 preset，每个的 YAML 都定义：

- `agents` — 角色列表：id, role, system_prompt, tools, skills, max_iterations, timeout_seconds, max_retries
- `tasks` — 任务 DAG：id, agent_id, prompt_template, depends_on, input_from
- `variables` — 用户模板变量

agents 的 `skills` 字段只是 whitelist（过滤 Available Skills 描述）。实际 skill 调用需要 agent 在 system_prompt 中说 "Use load_skill('technical-basic')"。
