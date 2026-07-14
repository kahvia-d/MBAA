# MBAA Pipeline 开发规范与最佳实践

本文用于统一 MBAA 的 MaaFramework Pipeline、识别素材、任务配置和异常恢复写法。目标不是追求最少节点，而是让每一步操作都能由画面状态证明成功，并在 loading、动画、点击失效、无可执行内容等情况下可预测地结束。

本文规则按以下优先级解释：

1. 当前项目使用的 MaaFramework Schema 和[任务流水线协议](../../3.1-%E4%BB%BB%E5%8A%A1%E6%B5%81%E6%B0%B4%E7%BA%BF%E5%8D%8F%E8%AE%AE.md)是字段语义的唯一依据。
2. 本文是 MBAA 的项目级约束，用于统一实现方式。
3. 其他 MaaFramework 应用和 MAA 官方项目只提供设计参考，不能覆盖当前 Schema。

文中的关键词含义如下：

- **必须**：新代码应满足；不满足时需要在 PR 中说明理由。
- **应该**：通常应采用；存在明确证据时可以选择其他实现。
- **可以**：按具体任务需要选用。

## 1. 核心原则

### 1.1 用状态证明操作成功

Pipeline 应写成有限状态机，而不是一串“点击坐标 + 等待时间”。每次关键操作后至少证明下列一项：

- 目标页面的稳定标志已经出现；
- 原页面或弹窗的稳定标志已经消失；
- 业务结果已经出现，例如最终奖励行、购买成功标题或无可领取提示；
- 已回到一个后续流程能够识别的已知页面。

固定坐标只负责执行操作，不能证明操作成功。即使点击动作返回成功，点击也可能发生在 loading、按钮动画或遮罩期间，游戏状态未必变化。

### 1.2 正常空状态不是异常

“无邮件可领取”“收益已领取”“商品售罄”“今日已签到”“没有摸头标志”等状态，应使用独立节点识别并进入正常结束分支。

不得用以下方式代替空状态：

- 等待按钮超时后无限重试；
- 超时后继续执行依赖该按钮成功的下一步；
- 在 `on_error` 中直接 `Stop`，掩盖仍停留在深层页面的事实。

### 1.3 重试必须有界

任何可能回到自身或上游节点的路径都必须回答两个问题：

1. 什么状态会结束重试？
2. 最多重试多少次或等待多久？

优先使用父节点的有限 `timeout`、节点的 `max_hit` 或显式的 `Retry1`、`Retry2` 节点。不得创建没有退出条件的自循环。

### 1.4 先复用公共状态，再编写任务状态

主界面确认、loading、Home、Back、通用确认、奖励关闭等交互，应集中在公共 Pipeline 中。业务 Pipeline 只描述任务特有状态。

公共节点必须满足：

- 名称带明确前缀，例如 `Nav`、`Common`；
- ROI 严格，不依赖全屏误匹配；
- 可以被多个任务安全调用；
- 不在多个文件中重复定义 `Stop` 或同名节点。

## 2. MaaFramework 节点语义

### 2.1 `next` 是有顺序的状态路由

框架按数组顺序识别当前节点的 `next`，每轮只执行第一个命中的节点。因此顺序本身就是业务策略。

推荐顺序：

1. 已经到达的最终或目标状态；
2. 必须优先处理的遮罩、弹窗或 loading；
3. 当前页面上的业务操作；
4. 重新进入或恢复操作。

如果两个模板可能同时命中，应把更具体、更安全的状态放在前面。不要依赖 JSON 对象中节点定义的先后顺序，只有 `next` 数组顺序参与路由。

### 2.2 `timeout` 属于当前节点对 `next` 的等待

`timeout` 控制的是：当前节点完成动作后，循环识别其 `next` 列表的总时间。它不控制当前节点作为候选项时被识别多久。

例如：

```json
{
    "OpenExamplePage": {
        "recognition": "TemplateMatch",
        "template": "example/open.png",
        "action": "Click",
        "timeout": 8000,
        "next": [
            "ExamplePageOpened"
        ]
    },
    "ExamplePageOpened": {
        "recognition": "TemplateMatch",
        "template": "example/title.png"
    }
}
```

这里的 `8000` 表示点击入口后最多等待 `ExamplePageOpened` 八秒。把 `timeout` 只写在 `ExamplePageOpened` 上，不能延长父节点等待它出现的时间。

建议范围不是硬性常量，应按实机数据调整：

| 场景 | 建议起点 |
| --- | --- |
| 可选按钮或可选弹窗探测 | 500-1500 ms |
| 普通按钮后的局部状态变化 | 1000-3000 ms |
| 页面跳转 | 3000-10000 ms |
| loading、扫荡结算、长动画 | 按实测设置独立长等待 |

不得为了“更稳”给所有节点统一设置数十秒 `timeout`。这会让正常空状态和识别失败都变成明显卡顿。

### 2.3 `rate_limit` 控制轮询频率

`rate_limit` 是每轮 `next` 识别的最低耗时。高频状态切换可以使用较短值，稳定页面不需要过度轮询。

- 快速 loading、按钮变为可点击：通常使用 100-300 ms。
- 普通页面状态：通常使用 300-1000 ms。
- OCR 或候选节点很多时，应避免过低值造成无意义的识别开销。

若大量节点重复相同值，可以在 `default_pipeline.json` 中集中配置；引入默认配置前必须完整回归现有任务，避免无意改变所有节点行为。

### 2.4 `on_error` 是失败收敛，不是第二份 `next`

当前节点动作失败，或其 `next` 在 `timeout` 内全部未命中，才会进入 `on_error`。

规则：

- `next` 和 `on_error` 不得包含同一目标，否则会触发 `Duplicate route`。
- `on_error` 应进入已知恢复状态、有限重试或明确失败出口。
- 业务失败时不得无条件 `Stop`；应先尝试回到主界面或可识别页面。
- `[JumpBack]` 位于错误处理路径时不会执行回跳，不要依赖它从 `on_error` 自动返回父节点。

### 2.5 `[JumpBack]` 用于处理后返回父状态机

`[JumpBack]Node` 命中后，会执行该节点及其后继链，然后返回当前父节点，重新从父节点 `next` 开始识别。适合：

- loading 短等待；
- 关闭一次性弹窗；
- 点击入口后重新确认目标页面；
- 在列表中处理一个项目后继续扫描。

不适合：

- 没有 `max_hit` 或父节点有限 `timeout` 的永久自循环；
- 处理后不会回到父页面的跨页面业务链；
- 需要从错误路径自动回跳的流程。

### 2.6 `max_hit`、`repeat`、`enabled`

- `max_hit`：限制节点可命中的次数，适合点击重试、滑动查找和有限轮询。超过次数后，该节点会被跳过。
- `repeat`：表示该节点动作的总执行次数，不是“额外增加的次数”。仅适合同一动作可以连续安全执行的场景。
- `enabled`：为 `false` 时，其他节点路由到该节点时会跳过它。适合由通用 UI 的 `pipeline_override` 开关可选分支。

如果每次点击后都可能出现弹窗、库存变化或按钮失效，不应使用 `repeat` 盲点，应把一次点击写成一个可验证的状态循环。

### 2.7 `inverse` 用于证明状态消失

关闭弹窗、退出奖励页和完成页面切换时，应复用弹窗标题或页面稳定模板，并设置 `inverse: true` 判断它已经消失。

`inverse` 的模板与 ROI 必须足够稳定。不要用会因按钮禁用、动画或颜色变化而自行消失的按钮模板证明整个弹窗关闭。

### 2.8 等待参数的使用边界

- `pre_wait_freezes`：动作前等待画面稳定。
- `post_wait_freezes`：动作后等待画面稳定，再识别 `next`。
- `pre_delay`、`post_delay`：固定延迟，仅在没有可靠视觉状态时少量使用。
- `repeat_wait_freezes`、`repeat_delay`：只影响 `repeat` 的第二次及后续动作。

`post_wait_freezes` 不是通用加速或防错开关。持续动画、粒子效果或角色待机可能让“画面稳定”比预期更晚。页面跳转和弹窗关闭应优先识别目标状态；只有确实需要等待局部动画静止时才设置较短值。

## 3. 标准状态模式

以下示例用于表达结构，节点名和素材路径需要按任务替换。所有示例均为合法 JSON。

### 3.1 可靠打开页面

入口节点同时考虑“已进入”“正在 loading”“入口仍可点击”，并通过有限超时收敛：

```json
{
    "StartExampleTask": {
        "timeout": 8000,
        "rate_limit": 250,
        "next": [
            "ExamplePageOpened",
            "[JumpBack]ExampleLoading",
            "[JumpBack]OpenExamplePage"
        ],
        "on_error": [
            "ReturnExampleTaskToMain"
        ]
    },
    "OpenExamplePage": {
        "recognition": "TemplateMatch",
        "template": "main_ui/example.png",
        "roi": [
            100,
            600,
            120,
            100
        ],
        "threshold": 0.62,
        "green_mask": true,
        "action": "Click",
        "max_hit": 3,
        "post_wait_freezes": 500
    },
    "ExampleLoading": {
        "recognition": "TemplateMatch",
        "template": "nav/loading.png",
        "roi": [
            500,
            300,
            280,
            120
        ],
        "threshold": 0.7,
        "action": "DoNothing",
        "max_hit": 30
    },
    "ExamplePageOpened": {
        "recognition": "TemplateMatch",
        "template": "example/page_title.png",
        "roi": [
            80,
            0,
            220,
            80
        ],
        "threshold": 0.75,
        "next": [
            "RunExamplePlan"
        ]
    }
}
```

入口点击重试用于应对 loading 恰好遮挡点击，但必须由 `max_hit` 和父节点 `timeout` 限制。

### 3.2 可选弹窗的四状态处理

动画弹窗必须区分：标题存在、按钮可点击、点击已执行、标题已消失。

```json
{
    "CheckOptionalDialog": {
        "timeout": 1200,
        "rate_limit": 200,
        "next": [
            "HandleOptionalDialog",
            "ExampleContentReady"
        ],
        "on_error": [
            "ContinueExampleWithoutDialog"
        ]
    },
    "HandleOptionalDialog": {
        "recognition": "TemplateMatch",
        "template": "example/dialog_title.png",
        "roi": [
            500,
            120,
            280,
            80
        ],
        "threshold": 0.78,
        "timeout": 12000,
        "rate_limit": 250,
        "next": [
            "OptionalDialogGone",
            "[JumpBack]ClickOptionalDialogConfirm"
        ],
        "on_error": [
            "ReturnExampleTaskToKnownState"
        ]
    },
    "ClickOptionalDialogConfirm": {
        "recognition": "TemplateMatch",
        "template": "example/dialog_confirm_enabled.png",
        "roi": [
            500,
            420,
            280,
            100
        ],
        "threshold": 0.8,
        "action": "Click",
        "max_hit": 4,
        "post_wait_freezes": 300
    },
    "OptionalDialogGone": {
        "recognition": "TemplateMatch",
        "template": "example/dialog_title.png",
        "roi": [
            500,
            120,
            280,
            80
        ],
        "threshold": 0.78,
        "inverse": true,
        "next": [
            "ExampleContentReady"
        ]
    }
}
```

关键点是：确认按钮未匹配只能表示按钮尚不可点击，不能表示弹窗不存在；弹窗是否关闭应由稳定标题消失来判断。

### 3.3 点击无效时重试关闭

奖励页可能先显示按钮，再逐项播放奖励动画。点击过早会无效，因此点击后要验证奖励标题消失：

```json
{
    "HandleRewardPage": {
        "timeout": 10000,
        "rate_limit": 250,
        "next": [
            "RewardPageGone",
            "[JumpBack]ClickRewardPage"
        ],
        "on_error": [
            "RecoverRewardPage"
        ]
    },
    "ClickRewardPage": {
        "recognition": "TemplateMatch",
        "template": "common/reward_title.png",
        "roi": [
            480,
            60,
            320,
            100
        ],
        "threshold": 0.78,
        "action": "Click",
        "target": [
            640,
            650,
            1,
            1
        ],
        "max_hit": 4,
        "post_wait_freezes": 300
    },
    "RewardPageGone": {
        "recognition": "TemplateMatch",
        "template": "common/reward_title.png",
        "roi": [
            480,
            60,
            320,
            100
        ],
        "threshold": 0.78,
        "inverse": true,
        "next": [
            "ContinueAfterReward"
        ]
    }
}
```

如果动画期间整个页面持续变化，不要给关闭节点设置很大的 `post_wait_freezes`；让“标题仍在/标题消失”的状态决定是否继续。

### 3.4 等待异步结算完成

扫荡、批量购买等流程中，确认按钮可能早于最终结果可操作。应等待只有结算完成后才出现的稳定内容：

```json
{
    "StartAsyncSettlement": {
        "recognition": "TemplateMatch",
        "template": "example/start.png",
        "action": "Click",
        "timeout": 60000,
        "rate_limit": 500,
        "next": [
            "SettlementFinalRow"
        ],
        "on_error": [
            "RecoverAsyncSettlement"
        ]
    },
    "SettlementFinalRow": {
        "recognition": "OCR",
        "roi": [
            180,
            470,
            420,
            160
        ],
        "expected": "最终|獲得獎勵",
        "timeout": 6000,
        "rate_limit": 250,
        "next": [
            "SettlementPageGone",
            "[JumpBack]ConfirmSettlement"
        ],
        "on_error": [
            "RecoverAsyncSettlement"
        ]
    },
    "ConfirmSettlement": {
        "recognition": "TemplateMatch",
        "template": "example/final_confirm.png",
        "roi": [
            500,
            560,
            280,
            130
        ],
        "threshold": 0.78,
        "action": "Click",
        "max_hit": 3,
        "post_wait_freezes": 300
    },
    "SettlementPageGone": {
        "recognition": "TemplateMatch",
        "template": "example/settlement_title.png",
        "roi": [
            480,
            80,
            320,
            100
        ],
        "threshold": 0.78,
        "inverse": true,
        "next": [
            "ContinueAfterSettlement"
        ]
    }
}
```

长 `timeout` 只放在真正的异步结算等待节点上。开始按钮、确认按钮等普通识别不应继承同样的长等待。

### 3.5 明确处理正常空状态

有内容和无内容都应是可识别的正常分支：

```json
{
    "CheckClaimPage": {
        "timeout": 2500,
        "rate_limit": 300,
        "next": [
            "ClaimAllAvailable",
            "ClaimPageEmpty"
        ],
        "on_error": [
            "RecoverUnknownClaimPage"
        ]
    },
    "ClaimAllAvailable": {
        "recognition": "TemplateMatch",
        "template": "example/claim_all.png",
        "action": "Click",
        "next": [
            "WaitClaimReward"
        ]
    },
    "ClaimPageEmpty": {
        "recognition": "TemplateMatch",
        "template": "example/nothing_to_claim.png",
        "next": [
            "ReturnExampleTaskToMain"
        ]
    }
}
```

如果游戏没有稳定的空状态素材，可以短时间探测操作按钮，然后进入一个明确命名的 `NoClaim` 分支；该分支仍要负责关闭窗口和回到已知页面。

### 3.6 返回主界面的收敛路由

返回流程应优先确认“已经在主界面”，再处理 loading、Home、Back。Home 与 Back 必须有严格且互不重叠的 ROI：

```json
{
    "ReturnExampleTaskToMain": {
        "timeout": 10000,
        "rate_limit": 250,
        "next": [
            "MainPageConfirmed",
            "[JumpBack]CommonLoading",
            "[JumpBack]CommonHomeButton",
            "[JumpBack]CommonBackButton"
        ],
        "on_error": [
            "RecoverReturnToMain"
        ]
    },
    "CommonHomeButton": {
        "recognition": "TemplateMatch",
        "template": "nav/home.png",
        "roi": [
            1215,
            0,
            65,
            65
        ],
        "threshold": 0.72,
        "green_mask": true,
        "action": "Click",
        "max_hit": 3
    },
    "CommonBackButton": {
        "recognition": "TemplateMatch",
        "template": "nav/back.png",
        "roi": [
            0,
            0,
            120,
            100
        ],
        "threshold": 0.72,
        "green_mask": true,
        "action": "Click",
        "max_hit": 5
    }
}
```

返回超时不应直接视为任务成功。恢复节点至少应记录失败并尝试回到一个已知页面；只有确认主界面稳定模板后才能进入全局 `Stop`。

## 4. 识别素材规范

### 4.1 模板选择

优先级从高到低：

1. 页面标题、固定文字、独特图标等稳定前景；
2. 不随数值、角色、奖励内容变化的固定边框或控件；
3. 经过 green mask 处理的透明 UI 前景；
4. 多背景模板或颜色过滤；
5. 降低阈值作为最后的辅助措施。

不得把大面积动态背景、角色立绘、变化数值或模糊阴影作为模板主体。

### 4.2 ROI

- 每个 TemplateMatch 和 OCR 都应该设置尽可能小的 ROI。
- Home、Back、关闭按钮等通用图标必须限制在它们实际出现的角落。
- ROI 应保留少量分辨率适配余量，但不能覆盖另一个相似图标可能出现的位置。
- 需要从匹配目标点击同一行其他按钮时，先在 1280x720 基准截图中测量，再使用 `target_offset`；实机日志必须验证最终点击框。

模板出现多个红框时，首先修正 ROI 和模板内容，不要用降低阈值或依赖默认候选排序掩盖问题。

### 4.3 阈值校准

阈值必须同时满足：不同背景下真目标可命中、相似控件和背景不会误命中。

建议流程：

1. 收集至少三张不同背景、不同动画阶段的截图；
2. 在固定 ROI 中测试匹配分数；
3. 收集容易混淆的负样本；
4. 在最低真阳性分数与最高假阳性分数之间留出余量；
5. 再决定是否使用 green mask 或模板变体。

主界面透明入口可以从约 `0.58-0.65` 开始调试，但这不是全局固定值。Home、Back 等高对比固定图标通常应使用更严格阈值。

### 4.4 OCR

- OCR ROI 只覆盖目标文本列，避免把标题、数量和按钮文字一起识别。
- `expected` 尽量使用锚定正则，例如 `^01$`，避免关号 `01` 误命中 `10` 或其他文本。
- 对已知的稳定误识别，可以在 `replace` 中集中修正；不得用宽泛正则吞掉未知结果。
- OCR 命中后点击同一行按钮时，必须验证 `target_offset` 在列表顶部、底部和滚动后都正确。

### 4.5 素材命名与归属

- 业务素材放在对应目录，例如 `cafe/`、`shop/`、`bounty/`。
- 真正通用的素材放在 `nav/` 或后续统一的 `common/`。
- 文件名描述视觉状态，而不是动作意图，例如 `purchase_success_title.png` 优于 `click_here.png`。
- 同一视觉状态只保留一个权威模板；确需多个版本时使用明确后缀并在节点中按优先级列出。

## 5. 任务与配置设计

### 5.1 任务拆分

一个日常任务建议拆为：

1. 入口与页面确认；
2. 可选弹窗处理；
3. 一个或多个独立业务子任务；
4. 结果确认；
5. 返回主界面。

入口和返回通常属于必须成功流程。某个奖励、某类商店或某个咖啡厅分店可以是允许跳过的子任务，但跳过后仍必须进入后续已知状态。

### 5.2 UI 配置与 Pipeline 分离

通用 UI 只负责表达用户选择，通过 `pipeline_override` 修改稳定节点；不要为每个选项复制整套 Pipeline。

```json
{
    "type": "select",
    "default_case": "不执行",
    "cases": [
        {
            "name": "不执行",
            "pipeline_override": {
                "RunExampleSubTask": {
                    "enabled": false
                }
            }
        },
        {
            "name": "执行 2 次",
            "pipeline_override": {
                "RunExampleSubTask": {
                    "enabled": true
                },
                "ClickExamplePlus": {
                    "enabled": true,
                    "repeat": 1
                }
            }
        }
    ]
}
```

配置规则：

- 消耗票券、货币或次数的功能默认关闭或设置为零。
- select、checkbox、input 的实际覆盖值必须处于 Pipeline 可接受范围。
- 多个选项修改同一节点时，要明确覆盖顺序，避免组合后状态不一致。
- 调试入口不得偷偷绕过用户配置；需要默认调试行为时应使用单独、明确命名的入口。

### 5.3 资源消耗任务

商店、扫荡等任务还必须满足：

- 选择目标使用白名单，未选择的项目绝不点击；
- 操作前确认仍在正确栏目、关卡或页面；
- 确认弹窗出现后再确认购买或扫荡；
- 等待最终结算状态，而不是看到早期确认按钮就继续；
- 余额不足、售罄、票券不足应进入安全跳过或错误恢复；
- 任何未知状态都不得盲点付费按钮。

### 5.4 何时使用 Agent

优先使用纯 Pipeline。出现以下情况时可以考虑 Agent：

- 多字段之间需要求和、互斥或动态约束；
- 需要根据识别结果计算坐标、数量或策略；
- 列表结构无法通过有限页和稳定节点表达；
- 需要维护跨多个页面的复杂运行状态；
- 纯 Pipeline 会产生大量重复节点且仍难以保证退出条件。

Agent 仍需遵守状态确认、有限重试和安全默认值规则。不得用 Agent 隐藏无法解释的点击序列。

## 6. 命名与文件组织

### 6.1 节点命名

使用“动作或状态 + 业务对象”的英文 PascalCase：

- 入口：`StartMailboxClaim`
- 页面状态：`WaitMailboxPageOpened`
- 业务动作：`ClickMailboxClaimAll`
- 结果状态：`WaitMailboxRewardClosed`
- 恢复：`RecoverMailboxUnknownState`
- 返回：`ReturnMailboxToMain`

避免 `Node1`、`Test2`、`DoSomething` 等无法表达状态的名称。重复页流程应保留类别或页码，例如 `WaitGeneralShopPage2RewardClosed`。

### 6.2 文件边界

- 一个业务任务一个主要 Pipeline 文件。
- 多任务共享的导航和通用交互放在公共文件。
- 不同文件的节点仍处于全局命名空间，新增前必须检查重名。
- `Stop` 只复用全局定义，不得在各业务文件重复定义。

### 6.3 注释与 `doc`

复杂节点应使用协议支持的 `doc` 字段说明设计意图，重点解释：

- 为什么该状态必须等待；
- 为什么使用较长 timeout；
- 为什么需要 inverse 或重试；
- 哪个截图和 UI 状态是模板来源。

注释应解释非显然原因，不要重复节点名已经表达的信息。

## 7. 常见反模式

### 7.1 固定点击后直接进入下一业务

错误：点击收益入口后直接点击“领取”，没有确认收益窗口出现。

后果：入口点击被 loading 吞掉时，后续坐标会点击咖啡厅场景中的其他位置。

正确做法：识别收益入口模板并点击，等待收益标题；未打开则有限重试入口。

### 7.2 用按钮未匹配证明弹窗关闭

错误：确认按钮未匹配就认为首次进入弹窗不存在。

后果：按钮可能仍处于灰色、动画阶段或换肤状态，弹窗本身仍在。

正确做法：稳定标题判断弹窗存在，可点击按钮判断动作时机，标题 `inverse` 判断关闭成功。

### 7.3 无限自循环

错误：找不到摸头标志时继续回到同一识别节点，没有 `max_hit` 或结束状态。

正确做法：摸头标志属于当前帧业务扫描，一次短探测未命中即可结束该店；页面 loading 的多轮轮询则有不同目的，但也必须受父节点 timeout 限制。

### 7.4 普遍使用长 timeout

错误：为普通按钮和可选功能统一设置 20-60 秒。

后果：已完成任务、无内容和模板失效都会表现为长时间停顿。

正确做法：短探测处理可选状态，只有真实异步结算使用独立长等待。

### 7.5 返回超时后直接成功

错误：`NavReturnToMain` 超时后进入 `Stop`。

后果：任务日志显示结束，但游戏仍停留在信箱、社团或弹窗页面，破坏下一个任务。

正确做法：只有主界面稳定模板命中后才能 `Stop`；超时进入明确恢复或报告失败。

### 7.6 全屏低阈值匹配通用图标

错误：Home 模板包含背景并在全屏搜索。

后果：页面中其他房屋形状或背景片段产生多个候选框，点击错误位置。

正确做法：去除背景、使用 green mask、限制右上角 ROI，并根据负样本提高阈值。

## 8. MBAA 落地优先级

本文不直接修改现有 Pipeline。后续规范化建议按以下顺序执行。

### P0：正确性与安全

- 所有循环补充明确退出状态和有限重试。
- 所有动画弹窗使用“稳定标题存在 + 按钮可点击 + 标题消失”三段确认。
- 商店、扫荡、奖励页点击后验证结果页消失。
- 为无邮件、无收益、无摸头标志、已完成等状态建立正常分支。
- 返回流程只有确认主界面后才结束任务，移除超时后静默成功。
- 检查所有 `next` 与 `on_error` 的重复目标。

### P1：公共能力与性能

- 继续收敛 `common_navigation.json`，统一 Home、Back、loading 和页面入口。
- 统计实机节点耗时，缩短普通按钮和可选状态的 timeout。
- 评估引入 `default_pipeline.json` 统一 `rate_limit` 等保守默认值，并完整回归。
- 重裁含背景的主界面、Home、Back 模板，建立不同大厅背景的模板回归集。
- 合并重复的奖励关闭、购买确认和扫荡确认结构。

### P2：工程保障

- 增加全局重复节点检查。
- 增加 `next` / `on_error` 交集检查。
- 增加无界自循环和缺少 `max_hit` 的风险检查。
- 对关键模板保存正负样本、ROI、阈值和匹配分数。
- 为需要复杂计算的功能建立 Agent 设计与测试约定。

## 9. 检查清单

### 9.1 开发前

- [ ] 已确认任务从哪个稳定页面启动、最终回到哪里。
- [ ] 已列出正常成功、正常无内容、loading、弹窗和未知状态。
- [ ] 已确认任务是否消耗货币、票券或次数，并设置安全默认值。
- [ ] 已检查公共 Pipeline 中是否已有可复用节点。
- [ ] 已准备不同背景和动画阶段的截图。

### 9.2 提交前

- [ ] 每个关键点击后都有目标出现或原状态消失的验证。
- [ ] 所有重试都有父节点 timeout、`max_hit` 或显式次数限制。
- [ ] `next` 顺序体现业务优先级。
- [ ] `next` 与 `on_error` 没有重复目标。
- [ ] 没有新增重复节点名或重复 `Stop`。
- [ ] TemplateMatch 和 OCR 使用了合理 ROI。
- [ ] Home、Back、关闭按钮不会在 ROI 内出现多个候选。
- [ ] 可选功能未出现时能快速跳过。
- [ ] 正常空状态不会进入错误死循环。
- [ ] 已运行 Schema 校验。

Schema 校验命令：

```powershell
python -X utf8 tools\validate_schema.py --schema-dir deps\tools --resource-dirs assets\resource --interface-files assets\interface.json
```

### 9.3 发布前

- [ ] 在当天首次执行和重复执行两种状态下测试。
- [ ] 在至少三种大厅背景下测试主界面入口。
- [ ] 测试点击恰好遇到 loading 的情况。
- [ ] 测试动画未结束时按钮点击无效的情况。
- [ ] 测试无可领取、售罄、次数不足等空状态。
- [ ] 测试任务完成后主界面稳定，再启动下一任务。
- [ ] 对消耗资源的任务先用最小次数和最小购买范围验证。
- [ ] 检查节点时间线，没有无理由的长等待。

## 10. 调研来源与可迁移经验

### MaaFramework

- [MaaFramework 仓库](https://github.com/MaaXYZ/MaaFramework)
- [任务流水线协议](https://maafw.com/docs/3.1-PipelineProtocol)
- [默认 Pipeline 示例](https://github.com/MaaXYZ/MaaFramework/blob/main/sample/resource/default_pipeline.json)

作为字段、节点流程和默认参数的权威来源。本文涉及 `next`、`timeout`、`on_error`、`JumpBack`、等待静止和默认 Pipeline 的语义均应以当前版本文档和仓库 Schema 为准。

### M9A

- [项目仓库](https://github.com/MAA1999/M9A)
- [default_pipeline.json](https://github.com/MAA1999/M9A/blob/main/resource/base/default_pipeline.json)
- [Combat 任务配置](https://github.com/MAA1999/M9A/blob/main/tasks/Combat.json)

可迁移经验：用 `default_pipeline.json` 统一保守默认参数；任务 UI 与 Pipeline 分离；通过 `pipeline_override` 把用户设置传给稳定节点；复杂关卡选择和停止条件再交给自定义逻辑。

### MAA_SnowBreak

- [项目仓库](https://github.com/overflow65537/MAA_SnowBreak)
- [通用导航与恢复](https://github.com/overflow65537/MAA_SnowBreak/blob/main/resource/base/pipeline/General.jsonc)
- [信箱流程](https://github.com/overflow65537/MAA_SnowBreak/blob/main/resource/base/pipeline/Mail.jsonc)

可迁移经验：给所有任务提供公共的“返回主菜单”收敛路径；显式识别空信箱等正常状态；已知弹窗优先关闭，未知状态最后才升级为重启应用。

### MaaGF2Exilium

- [项目仓库](https://github.com/DarkLingYun/MaaGF2Exilium)
- [公共控制按钮](https://github.com/DarkLingYun/MaaGF2Exilium/blob/main/assets/resource/base/pipeline/public/controlButton.json)
- [扫荡弹窗处理](https://github.com/DarkLingYun/MaaGF2Exilium/blob/main/assets/resource/base/pipeline/public/AutoSweepBattle/popup.json)
- [邮件领取](https://github.com/DarkLingYun/MaaGF2Exilium/blob/main/assets/resource/base/pipeline/public/PrepareDailyTasks/Email/getNewEmails.json)

可迁移经验：公共按钮和页面导航独立成层；对灰色、黑色等视觉变体使用严格 ROI 和多个模板；扫荡数量和弹窗状态通过识别推进；领取按钮可在验证结果后有限重试，并为“没有未领取内容”建立独立状态。

### MaaGakumasu

- [项目仓库](https://github.com/SuperWaterGod/MaaGakumasu)
- [基础 Pipeline](https://github.com/SuperWaterGod/MaaGakumasu/tree/main/assets/resource/base/pipeline)

可迁移经验：把通用工具节点与业务任务分层，保持任务配置和 Pipeline 资源边界清晰。项目实现只能作为案例，字段仍需按 MBAA 当前 Schema 复核。

### MaaAssistantArknights

- [dev-v2 分支](https://github.com/MaaAssistantArknights/MaaAssistantArknights/tree/dev-v2)
- [StartUpTask](https://github.com/MaaAssistantArknights/MaaAssistantArknights/blob/dev-v2/src/MaaCore/Task/Interface/StartUpTask.cpp)
- [FightTask](https://github.com/MaaAssistantArknights/MaaAssistantArknights/blob/dev-v2/src/MaaCore/Task/Interface/FightTask.cpp)
- [RecruitTask](https://github.com/MaaAssistantArknights/MaaAssistantArknights/blob/dev-v2/src/MaaCore/Task/Interface/RecruitTask.cpp)
- [MallTask](https://github.com/MaaAssistantArknights/MaaAssistantArknights/blob/dev-v2/src/MaaCore/Task/Interface/MallTask.cpp)
- [InfrastTask](https://github.com/MaaAssistantArknights/MaaAssistantArknights/blob/dev-v2/src/MaaCore/Task/Interface/InfrastTask.cpp)

可迁移经验：将大任务拆成必须成功的入口与允许失败的可选子任务；为参数设置类型、范围和兼容性校验；用次数限制控制药剂、购买和战斗；只有在已知恢复路径失败后才进行有限重启。MAA 的 C++ 任务层与 MaaFramework Pipeline 不是同一种接口，不应直接照搬字段或类结构。

## 11. 维护要求

- MaaFramework 版本或 Schema 更新后，应复核本文涉及的字段语义。
- 新增通用交互模式时，先补充本文，再在多个任务中复用。
- 实机日志证明现有建议不适用时，应记录截图、节点时间线和新方案，避免只通过增加 timeout 临时掩盖问题。
- 项目完成 P0/P1 重构后，应更新“落地优先级”，删除已经失效的现状描述。
