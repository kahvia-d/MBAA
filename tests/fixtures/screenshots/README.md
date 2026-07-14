# 运行时模板来源截图

本目录保存用于裁剪、校准和回归测试的 1280x720 原始截图。它不属于
`assets/resource`，因此不会被安装脚本打入发布包。

| 来源截图 | 主要运行时模板 |
| --- | --- |
| `主界面.png`、`主界面1.png`、`主界面2.png`、`主界面3.png` | `main_ui/*` |
| `任务界面.png` | `tasks/bounty.png`、`tasks/school_communication.png` |
| `悬赏通缉列表.png` | `bounty/road.png`、`bounty/railway.png`、`bounty/classroom.png`、`nav/home.png`、`nav/back.png` |
| `学园交流会.png` | `school_communication/trinity.png`、`school_communication/gehenna.png`、`school_communication/millennium.png`、`nav/home.png`、`nav/back.png` |
| `入场界面.png` | 关号 OCR ROI 与入场按钮偏移校准 |
| `扫荡界面.png` | `common/sweep_plus.png`、`common/sweep_start.png`、`common/sweep_info_close.png` |
| `确认扫荡.png` | `common/sweep_start_confirm.png` |
| `扫荡完成.png` | `common/sweep_complete_final.png` |
| `商店界面.png`、`商店界面战术大赛.png`、`商店列表含未选中战术大赛.png` | `shop/general_tab.png`、`shop/tactical_contest_tab.png` |
| `商店勾选物品.png` | `shop/select_purchase.png` |
| `商店购买确认.png` | `shop/purchase_confirm.png` |
| `商店购买成功.png` | `common/reward_success.png`、`shop/purchase_success_continue.png` |
| `社交.png`、`社团签到奖励.png` | `club/*` |
| `购买青辉石界面.png`、`购买青辉石界面组合包栏.png`、`购买每日免费组合包界面.png` | `pyroxene_purchase/*` |
| `信箱界面.png` | `mail/*` |
| `咖啡厅界面.png`、`首次进入咖啡厅.png`、`好感升级界面.png` | `cafe/cafe_title.png`、首次进入弹窗和摸头模板 |
| `咖啡厅收益界面.png`、`咖啡厅收益无可领取的内容.png` | `cafe/income_*` |
| `loading.png` | `nav/loading.png` |

`../reference_templates/` 保存暂未被 Pipeline 引用、但可能用于后续功能的历史裁剪模板。
