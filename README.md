<!-- markdownlint-disable MD033 MD041 -->
<p align="center">
  <img alt="LOGO" src="https://cdn.jsdelivr.net/gh/MaaAssistantArknights/design@main/v1/icons/maa-logo_512x512.png" width="256" height="256" />
</p>

<div align="center">

# MBAA

</div>

MBAA 是基于 [MaaFramework](https://github.com/MaaXYZ/MaaFramework) 的蔚蓝档案日常自动化项目。

> **MaaFramework** 是基于图像识别技术、运用 [MAA](https://github.com/MaaAssistantArknights/MaaAssistantArknights) 开发经验去芜存菁、完全重写的新一代自动化黑盒测试框架。
> 低代码的同时仍拥有高扩展性，旨在打造一款丰富、领先、且实用的开源库，助力开发者轻松编写出更好的黑盒测试程序，并推广普及。

## 安装与运行

1. 从 [GitHub Releases](https://github.com/kahvia-d/MBAA/releases) 下载与系统和架构匹配的 `MBAA-*` 压缩包。
2. 解压到独立目录，启动包内的 MFAAvalonia 图形界面。
3. 连接模拟器、Android 设备或游戏窗口，选择任务和配置后运行。

当前脚本以 1280x720 为坐标基准，游戏界面语言应与项目素材一致。执行任务前建议停留在主界面；脚本会在任务完成后确认返回主界面，再继续队列中的下一项。

## 支持任务

- 悬赏通缉：高架公路、沙漠铁道、教室的指定关号和扫荡次数。
- 学园交流会：三一、格黑娜、千禧的指定关号和扫荡次数。
- 商店购买：一般商店与战术大赛商店的独立格子选择。
- 社团签到。
- 购买每日免费组合包。
- 信箱一次领取。
- 咖啡厅日常：1、2 号店摸头与 1 号店收益领取。

邀请学生功能暂未开放。消耗票券或货币的选项默认关闭，请在运行前核对关号、次数和商品格子。

## 问题反馈

请通过 [GitHub Issues](https://github.com/kahvia-d/MBAA/issues) 提交问题，并附上：

- MBAA 版本、系统、控制器类型和实际分辨率。
- 任务名称与完整配置。
- MFAAvalonia 日志和节点时间线截图。
- 出错前后的游戏截图；请遮盖账号等隐私信息。
- 问题是否稳定复现，以及当天是否已经领取过对应奖励。

## 开发

请先阅读[如何开发](./docs/zh_cn/develop/how_to_develop.md)。

编写或维护任务流水线前，请阅读 [Pipeline 开发规范与最佳实践](./docs/zh_cn/develop/pipeline_best_practices.md)。

提交改动前，请阅读 [PR 规范](./docs/zh_cn/develop/pull_request_guidelines.md)。

## 生态共建

MAA 正计划建设为一类项目，而非舟的单一软件。

欢迎在 [社区项目列表](https://github.com/MaaXYZ/MaaFramework#%E7%A4%BE%E5%8C%BA%E9%A1%B9%E7%9B%AE) 中了解更多 MaaFramework 项目。

生成资源请修改 `tools/resource_specs/resources.json`，然后运行：

```bash
python tools/generate_resources.py --write
python tools/generate_resources.py --check
python tools/check_pipeline.py
```

## 常见问题

请阅读[常见问题](./docs/zh_cn/develop/faq.md)

## 鸣谢

本项目由 **[MaaFramework](https://github.com/MaaXYZ/MaaFramework)** 强力驱动！

感谢 MaaFramework 社区对底层框架和生态的贡献：

[![Contributors](https://contrib.rocks/image?repo=MaaXYZ/MaaFramework&max=1000)](https://github.com/MaaXYZ/MaaFramework/graphs/contributors)
