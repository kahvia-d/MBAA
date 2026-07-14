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
| `商店购买成功.png` | `common/reward_success.png`、`common/reward_continue.png` |
| `社交.png`、`社团签到奖励.png` | `club/*` |
| `购买青辉石界面.png`、`购买青辉石界面组合包栏.png`、`购买每日免费组合包界面.png` | `pyroxene_purchase/*` |
| `信箱界面.png` | `mail/*` |
| `咖啡厅界面.png`、`首次进入咖啡厅.png`、`咖啡厅访问学生目录灰色确认.png`、`好感升级界面.png` | `cafe/cafe_title.png`、`cafe/first_enter_confirm.png`、`cafe/first_enter_confirm_disabled.png`、首次进入弹窗标题和摸头模板 |
| `咖啡厅收益界面.png`、`咖啡厅收益无可领取的内容.png` | `cafe/income_*` |
| `课程表首页.png`、`课程表地区之一示例.png`、`含较清晰右侧箭头的图片.png`、`夏莱办公室.png`、`狂猎综合艺术区.png` | `main_ui/schedule.png`、`schedule/home_*`、`schedule/region_*`、`schedule/next_region_arrow.png`、地区首尾模板 |
| `当前地区全体课程表.png`、`含上完课学生的全体课程表（上完课的学生图标右上标会打绿色的勾）.png` | `schedule/all_schedule_*`、`schedule/heart.png`、`schedule/completed_check.png` |
| `课程表资讯.png`、`课程表报告.png`、`特殊学生列表.png` | `schedule/info_*`、`schedule/report_*`、`schedule/special_students/*` |
| `loading.png` | `nav/loading.png` |

`../reference_templates/` 保存暂未被 Pipeline 引用、但可能用于后续功能的历史裁剪模板。
