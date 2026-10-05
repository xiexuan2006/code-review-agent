@echo off
title ������� Agent
cd /d %~dp0
echo ��������������� Agent ͼ�ν���...
echo ��������������Զ��� http://127.0.0.1:7860
echo �رձ����ڼ���ֹͣ����
echo.
.venv\Scripts\python.exe web\app.py
pause
