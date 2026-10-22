# Codex 过程回复记录器

已制作并安装本地 Codex 插件 `codex-progress-recorder@personal`。插件读取 Codex Desktop 会话里可见的过程回复（截图中框出的文字），按时间导出为 Markdown。只读 Codex 日志，不修改会话。

## 自动记录

插件在 `SessionStart` 创建或刷新记录，在每轮任务的 `Stop` 时刷新，并在 `SessionEnd` 最后导出一次。为覆盖安装插件前就已打开的聊天，还安装了本地监视器：它在 Windows 登录后自动启动，每两秒检查最近两天的会话日志。过程回复和最终回复按时间顺序写进同一个文件，并用标题区分。每个聊天任务一个文件，默认保存在该会话项目文件夹的 `Codex过程记录\<会话ID>.md`。没有可用项目路径的聊天回退到用户文档目录。设置环境变量 `CODEX_PROGRESS_OUTPUT_DIR` 可统一覆盖默认目录。

安装后需要重启 Codex Desktop，并在首次出现的钩子信任提示中审核、信任这三个本地钩子。Codex 对插件钩子默认不自动信任；在完成该审核前，钩子不会运行，但监视器仍会自动记录。`SessionEnd` 可能在关闭应用、归档聊天，或聊天不再打开且空闲一段时间后才触发。

监视器启动项为当前用户注册表 `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` 下的 `CodexProgressRecorder`。卸载时应删除该启动项并结束对应的 `pythonw.exe` 进程，然后运行 `codex plugin remove codex-progress-recorder@personal`。

插件源文件在 [plugin](./plugin)；已复制到个人插件市场并通过 `codex plugin add codex-progress-recorder@personal` 安装。

## 手动导出

需要 Python 3.9 或更新版本，无第三方依赖。

```powershell
python .\codex_progress.py --list
python .\codex_progress.py --output .\progress.md
python .\codex_progress.py --session <会话ID> --output .\progress.md
python .\codex_progress.py --follow --output .\progress-live.md
```

默认选择最近修改的会话；`--follow` 每秒检查新增内容，按 Ctrl+C 停止。`--session` 也可传完整 `.jsonl` 路径。

只导出用户能看到的过程回复和最终回复，不导出内部推理、用户消息或命令输出。当前支持未压缩的 `.jsonl` 会话；较早的 `.jsonl.zst` 归档暂不支持。导出文件可能包含会话中的敏感文字，请自行决定存放位置。
