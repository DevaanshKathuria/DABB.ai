# Deployment Notes

The repository is configured to run as a public Streamlit app.

## Supported entrypoints
- `streamlit_app.py` is the default hosted entrypoint.
- `app.py` remains the reusable application module for local development and tests.

## Public host settings
- Streamlit Community Cloud: use `streamlit_app.py` as the main file.
- Render: use the included `render.yaml` or `Procfile`.
- Both deployment paths rely on `requirements.txt` at the repository root.

## Sanity checks
Run these before publishing a release:

```bash
python3 -m compileall app.py streamlit_app.py src tests
python3 -m pytest -q
streamlit run streamlit_app.py
```

## Notes
- The app falls back to bundled demo data if the primary training CSV is unavailable.
- The model cache is stored under `models/` during local runs and can be regenerated automatically.
