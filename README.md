# RC coal silo design dashboard

## Run
```
pip install -r requirements.txt
streamlit run app.py
```
The browser opens automatically (otherwise go to http://localhost:8501).

## Files
- `app.py`        Streamlit dashboard (inputs, tabs, graphs, 3D model)
- `silo_calc.py`  Calculation engine: formulas copied from `silo_design.py`
- `silo_design.py` Your original script, unchanged (still runs on its own)
- `tests/`        `python tests/test_silo_calc.py` and `python tests/test_app.py`

## Notes
- Edits in the sidebar are applied when you press **Calculate Design**.
- `fck` is an input but, as in the original script, no formula uses it.
- Hopper bars in the 3D view default to Method A spacing, as in the original 3D figure.
