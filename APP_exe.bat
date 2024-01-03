@echo off

set conda_environment=dataViz

rem Activate the Conda environment
call conda activate %conda_environment%

python sensor_connect_app.py

rem Deactivate the Conda environment (optional)
call conda deactivate
