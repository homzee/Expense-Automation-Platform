# 自动化财务报销系统：架构评估与全栈Python实现建议

## 1. 背景与目标
本报告基于现有需求描述，总结了自动化生成 “Tina Claim Form” 报销单的总体方案，并对其架构健壮性、落地可行性与后续优化方向进行评估。目标是在**OCR JSON**与**ETC/充电 Excel**多源数据融合的前提下，输出符合“每页 10 行交易”限制的高保真报销 Excel 文件。

## 2. 现有方案亮点
- **ETL 分层清晰**：抽取（OCR/Excel）→ 转换（标准化模型、汇率与 GST 计算、分页）→ 加载（openpyxl 填充模板）。
- **强类型数据模型**：使用 `pydantic` 定义 `ExpenseItem`/`ClaimHeader`，结合 `Decimal` 控制精度，符合财务场景需求。
- **适配器模式**：通过 `ExcelSourceReader` 统一读取 ETC/充电账单，降低新增数据源的改动成本。
- **分页算法**：按日期排序并以 10 行为一批复制模板 Sheet，满足 Note 3 的格式约束。

## 3. 风险与改进建议
| 领域 | 现状风险 | 改进建议 |
| --- | --- | --- |
| 模板耦合 | 行号/列号写死，模板变更即失效 | 在模板中使用命名范围或隐藏的锚点单元格，通过名称解析坐标；在加载时校验关键单元格是否存在。 |
| 数据质量 | 依赖源数据格式正确，异常仅打印 | 在 `ExcelSourceReader` 中加入必填列校验与异常汇总报告；对金额/日期增加自动修复与失败清单。 |
| 汇率获取 | 静态汇率，无法反映交易日 | 抽象 `ForexProvider` 接口，默认使用固定值，生产配置可接 Oanda/ECB API 并带缓存。 |
| 测试覆盖 | 缺少自动化验证 | 编写 `pytest` 用例，覆盖：模型校验、金额精度（3 位小数）、分页清空空行、模板不存在/被占用的错误处理。 |
| 性能与并发 | 单线程文件写入，无法防止并发冲突 | 输出临时文件后原子移动，或使用时间戳命名避免覆盖；为 Web 场景准备队列/锁机制。 |

## 4. 推荐的模块化目录结构
```text
src/
  models.py          # Pydantic 数据模型与财务计算
  ingestion/
    ocr_adapter.py   # OCR JSON → ExpenseItem 列表
    excel_reader.py  # ExcelSourceReader 通用读取器
  rendering/
    claim_writer.py  # 分页与模板填充引擎
  services/
    forex.py         # ForexProvider 接口与实现
    orchestrator.py  # 组装流程，聚合多源并驱动输出
  cli.py             # 命令行入口，支持输入/输出路径参数
tests/
  test_models.py
  test_rendering.py
  test_excel_reader.py
```

## 5. 关键实现要点
1. **金额精度策略**：
   - 输入阶段统一去除千分位与货币符号；
   - 中间计算使用 `Decimal` 并量化到 4 位小数，最终报表量化到 3 位以匹配样例。
2. **分页与空行清理**：
   - 通过 `math.ceil(len(items)/10)` 计算页数；
   - 每页填充后对剩余行调用 `_clear_row` 确保无遗留示例值。
3. **模板加载与复制**：
   - 首次加载模板并重命名为 `Page_1`；
   - 后续页使用 `copy_worksheet`，并在写入前调用头/尾渲染函数补齐日期、部门、审批人。
4. **数据源扩展**：
   - `ExcelSourceReader` 接受列映射与静态字段；
   - 支持日期字符串、`Timestamp` 自动转换，缺失列时给出警告并跳过。
5. **可观测性**：
   - 建议引入结构化日志（如 `structlog`）输出批次大小、失败行与汇率来源；
   - 生成完成后打印输出路径与页数。

## 6. 最小可行实现（MVP）路线
1. 落地 `src/models.py` 与 `src/ingestion/excel_reader.py`，打通 ETC/充电数据读取并生成 `ExpenseItem`。
2. 实现 `src/rendering/claim_writer.py`，硬编码坐标先满足当前模板，后续再改命名范围。
3. 在 `src/services/orchestrator.py` 中串起 OCR mock、Excel 读取与分页写入；CLI 参数包含模板路径、输出路径与数据源文件。
4. 编写基础测试用例验证分页与金额精度，确保无回归。

## 7. 结论
现有方案在架构分层、模型设计与分页策略上已经覆盖核心业务需求。若按本报告的目录与改进建议推进，可较快产出一版可交付的工业级 Python 实现，同时为后续集成汇率服务、Web 入口与模板演进预留扩展空间。
