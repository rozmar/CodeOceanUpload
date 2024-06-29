@echo off
REM Activate the conda environment
CALL conda activate bci_with_suite2p

REM Run the Python script with arguments
python %1 %2 %3

REM Deactivate the conda environment (optional)
CALL conda deactivate