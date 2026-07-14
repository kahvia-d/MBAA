# 未启用模板

这些模板当前没有任何 Pipeline 引用，因而从 `assets/resource/image` 移出，
避免进入发布包。恢复某项功能时，应先将对应文件移回运行时素材目录，补充
严格 ROI，并通过 Pipeline 静态检查。
