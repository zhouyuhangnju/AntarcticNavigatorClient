git

@echo off
color 0b

:zhu
cls
echo ===================================
echo 1. 路径规划   2. 图片请求   3. 退出
echo ===================================

set /p choice= 请选择要运行的应用：
if /i %choice% == 1 goto a
if /i %choice% == 2 goto b
if /i %choice% == 3 goto c
echo 你的输入有误，按任意键返回主程序
pause >> nul
goto zhu
cls
:a
goto zhu
:b
goto zhu
:c
exit
