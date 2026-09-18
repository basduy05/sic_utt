@echo off
echo Running migrate_sic_to_lexicon.py...
python scripts\migrate_sic_to_lexicon.py
if %ERRORLEVEL% NEQ 0 (
    echo Migration failed.
    exit /b %ERRORLEVEL%
)

echo.
echo Running retrain_phase2_classifiers.py...
python scripts\retrain_phase2_classifiers.py
if %ERRORLEVEL% NEQ 0 (
    echo Tabular/NLP Classifier retraining failed.
    exit /b %ERRORLEVEL%
)

echo.
echo Running train_phobert_ner_local.py...
python scripts\train_phobert_ner_local.py
if %ERRORLEVEL% NEQ 0 (
    echo PhoBERT NER training failed.
    exit /b %ERRORLEVEL%
)

echo.
echo ALL TRAINING TASKS COMPLETED SUCCESSFULLY.
