# 未启用模板

这些模板当前没有任何 Pipeline 引用，因而从 `assets/resource/image` 移出，
避免进入发布包。恢复某项功能时，应先将对应文件移回运行时素材目录，补充
严格 ROI，并通过 Pipeline 静态检查。

`schedule_special_students/` 保存课程表特殊学生的大尺寸源头像，由
`tools/generate_schedule_templates.py` 生成运行时使用的 `43x52` green-mask 模板。
若某名学生在 `schedule_special_students_actual/` 中存在实机课程表尺寸模板，生成器
会优先使用该模板，避免大头像缩放后产生构图偏差。
同一脚本还会从 `tests/fixtures/screenshots/当前地区全体课程表.png` 生成已遮蔽
羁绊数字的通用 `schedule/heart.png`，避免不同羁绊等级造成匹配失败。
