@echo off
REM 考试质量分析系统 - PostgreSQL 数据库备份脚本
REM 用法: backup.bat
REM 建议通过 Windows 任务计划程序每天运行

set BACKUP_DIR=.\backups
set DB_NAME=examdb
set DB_USER=examuser
set DB_PASS=exampass
set DB_HOST=localhost
set DB_PORT=5432
set RETENTION_DAYS=30

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

set DATE_TAG=%date:~0,4%%date:~5,2%%date:~8,2%
set FILENAME=%BACKUP_DIR%\%DB_NAME%_%DATE_TAG%.sql

echo [%date% %time%] Starting backup of %DB_NAME%...
set PGPASSWORD=%DB_PASS%
pg_dump -h %DB_HOST% -p %DB_PORT% -U %DB_USER% %DB_NAME% > "%FILENAME%"

if %ERRORLEVEL% EQU 0 (
    echo [%date% %time%] Backup saved to %FILENAME%
    
    REM 压缩备份
    gzip "%FILENAME%"
    echo [%date% %time%] Backup compressed
    
    REM 删除30天前的旧备份
    forfiles /p "%BACKUP_DIR%" /m *.gz /d -%RETENTION_DAYS% /c "cmd /c del @file" 2>nul
    echo [%date% %time%] Old backups cleaned (retention: %RETENTION_DAYS% days)
) else (
    echo [%date% %time%] Backup FAILED!
    exit /b 1
)

echo [%date% %time%] Backup completed successfully
