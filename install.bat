@echo off
REM HowTimeFly 依赖安装脚本 - 使用国内镜像加速

echo ========================================
echo   HowTimeFly 依赖快速安装
echo ========================================
echo.

REM 使用清华镜像源加速
echo [1/3] 使用清华镜像源安装依赖...
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

if errorlevel 1 (
    echo.
    echo [!] 安装失败，尝试使用阿里云镜像...
    pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
)

if errorlevel 1 (
    echo.
    echo [!] 安装失败，尝试使用官方源（可能较慢）...
    pip install -r requirements.txt
)

if errorlevel 1 (
    echo.
    echo [X] 安装失败，请检查网络或手动安装
    pause
    exit /b 1
)

echo.
echo [2/3] 验证安装...
python -c "import fastapi, uvicorn, sqlalchemy, PIL, piexif, yaml" 2>nul
if errorlevel 1 (
    echo [!] 验证失败，请检查安装
    pause
    exit /b 1
)

echo.
echo [3/3] 生成测试数据...
python scripts\create_test_data.py

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 下一步:
echo   1. python scripts\init_db.py    - 初始化数据库
echo   2. python scripts\scan.py       - 扫描媒体文件
echo   3. python run.py                - 启动服务
echo   4. 访问 http://127.0.0.1:8080
echo.
pause
