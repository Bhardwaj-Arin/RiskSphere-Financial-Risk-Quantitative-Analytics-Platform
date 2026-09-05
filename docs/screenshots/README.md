# Dashboard screenshots

The source package does not include a fabricated Streamlit screenshot. Generate screenshots from the actual running workbench after installation:

```bash
python scripts/run_pipeline.py
streamlit run dashboard/app.py
```

Capture at least:

1. Executive Overview
2. Market Risk
3. Backtesting
4. Credit Risk
5. Model Validation
6. Risk Limits

This keeps portfolio screenshots tied to an actual executable run rather than a static mock-up.
