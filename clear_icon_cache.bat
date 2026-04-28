@echo off
echo 正在清理Windows图标缓存...
taskkill /f /im explorer.exe
echo 正在删除图标缓存文件...

del "%localappdata%\IconCache.db" /a
del "%localappdata%\Microsoft\Windows\Explorer\iconcache*" /a
del "%localappdata%\Microsoft\Windows\Explorer\thumbcache*" /a

echo 正在重启资源管理器...
start explorer.exe
echo 完成！请重新运行你的应用程序。
pause