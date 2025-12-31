@echo off
chcp 65001 >nul

echo.
echo ===================================================
echo   IPTV v3.1.0 - 项目文件清理工具
echo ===================================================
echo.

echo 此脚本将删除不再需要的文件，包括：
echo   - 重复的旧文档 (8个)
echo   - 临时测试文件 (6个)
echo   - 失败的打包脚本 (5个)
echo   - 开发过程文档 (5个)
echo.
echo 总计约删除 24-30 个文件
echo.

set /p confirm="确认执行清理? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo 已取消清理
    pause
    exit /b 0
)

echo.
echo 开始清理...
echo ===================================================

REM 删除重复的旧文档
echo [1/4] 清理重复文档...
if exist "FINAL_SUMMARY.md" del /f "FINAL_SUMMARY.md" && echo   ✓ FINAL_SUMMARY.md
if exist "QUICK_REFERENCE.md" del /f "QUICK_REFERENCE.md" && echo   ✓ QUICK_REFERENCE.md
if exist "README.md" del /f "README.md" && echo   ✓ README.md
if exist "MODIFICATION_COMPLETE.md" del /f "MODIFICATION_COMPLETE.md" && echo   ✓ MODIFICATION_COMPLETE.md
if exist "VERIFICATION_REPORT.md" del /f "VERIFICATION_REPORT.md" && echo   ✓ VERIFICATION_REPORT.md
if exist "REFACTORING_COMPLETE.md" del /f "REFACTORING_COMPLETE.md" && echo   ✓ REFACTORING_COMPLETE.md
if exist "ERROR_FIX_SUMMARY.md" del /f "ERROR_FIX_SUMMARY.md" && echo   ✓ ERROR_FIX_SUMMARY.md
if exist "COMPLETE_LOG_DISPLAY_SUMMARY.md" del /f "COMPLETE_LOG_DISPLAY_SUMMARY.md" && echo   ✓ COMPLETE_LOG_DISPLAY_SUMMARY.md

REM 删除测试文件
echo.
echo [2/4] 清理测试文件...
if exist "test_api_execute.py" del /f "test_api_execute.py" && echo   ✓ test_api_execute.py
if exist "test_api_routes.py" del /f "test_api_routes.py" && echo   ✓ test_api_routes.py
if exist "test_error_messages.py" del /f "test_error_messages.py" && echo   ✓ test_error_messages.py
if exist "test_execute_task.py" del /f "test_execute_task.py" && echo   ✓ test_execute_task.py
if exist "test_log_filter.js" del /f "test_log_filter.js" && echo   ✓ test_log_filter.js
if exist "test_schedule_api.py" del /f "test_schedule_api.py" && echo   ✓ test_schedule_api.py

REM 删除失败的打包脚本
echo.
echo [3/4] 清理失败的打包脚本...
if exist "build_release.py" del /f "build_release.py" && echo   ✓ build_release.py
if exist "simple_pack.py" del /f "simple_pack.py" && echo   ✓ simple_pack.py
if exist "simple_pack.bat" del /f "simple_pack.bat" && echo   ✓ simple_pack.bat
if exist "iptv-server.spec" del /f "iptv-server.spec" && echo   ✓ iptv-server.spec
if exist "iptv-server-3.1.0.spec" del /f "iptv-server-3.1.0.spec" && echo   ✓ iptv-server-3.1.0.spec

REM 删除开发过程文档
echo.
echo [4/4] 清理开发文档...
if exist "DASHBOARD_LOG_FIX.md" del /f "DASHBOARD_LOG_FIX.md" && echo   ✓ DASHBOARD_LOG_FIX.md
if exist "DASHBOARD_LOG_FIX_CHECKLIST.md" del /f "DASHBOARD_LOG_FIX_CHECKLIST.md" && echo   ✓ DASHBOARD_LOG_FIX_CHECKLIST.md
if exist "DASHBOARD_LOG_QUICK_GUIDE.md" del /f "DASHBOARD_LOG_QUICK_GUIDE.md" && echo   ✓ DASHBOARD_LOG_QUICK_GUIDE.md
if exist "LOG_DISPLAY_FIX_COMPLETE.md" del /f "LOG_DISPLAY_FIX_COMPLETE.md" && echo   ✓ LOG_DISPLAY_FIX_COMPLETE.md
if exist "LOG_DISPLAY_VISUAL_GUIDE.md" del /f "LOG_DISPLAY_VISUAL_GUIDE.md" && echo   ✓ LOG_DISPLAY_VISUAL_GUIDE.md

echo.
echo ===================================================
echo ✅ 清理完成！
echo.
echo 已删除不必要的文件，保留核心文件：
echo   ✓ app_new.py (应用入口)
echo   ✓ config.py (配置)
echo   ✓ make_release.py (打包脚本)
echo   ✓ README_FINAL.md (项目说明)
echo   ✓ PACKAGING_COMPLETE.md (打包说明)
echo   ✓ 以及其他核心文件...
echo.
echo 建议：运行 python app_new.py 测试应用是否正常
echo.
pause
