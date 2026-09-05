-- RiskSphere PostgreSQL reference schema.
-- Educational portfolio project; not a production bank risk-data model.

CREATE TABLE IF NOT EXISTS model_runs (
    run_id          VARCHAR(64) PRIMARY KEY,
    executed_at     TIMESTAMP NOT NULL,
    model_version   VARCHAR(32) NOT NULL,
    data_source     VARCHAR(128) NOT NULL,
    data_version    VARCHAR(64),
    git_commit      VARCHAR(64),
    status          VARCHAR(32) NOT NULL
);

CREATE TABLE IF NOT EXISTS market_prices (
    run_id          VARCHAR(64) NOT NULL REFERENCES model_runs(run_id),
    date            DATE NOT NULL,
    risk_factor     VARCHAR(64) NOT NULL,
    value           DOUBLE PRECISION NOT NULL,
    source          VARCHAR(128) NOT NULL,
    retrieved_at    TIMESTAMP,
    PRIMARY KEY (run_id, date, risk_factor)
);
CREATE INDEX IF NOT EXISTS idx_market_prices_factor_date ON market_prices(risk_factor, date);

CREATE TABLE IF NOT EXISTS portfolio_positions (
    run_id          VARCHAR(64) NOT NULL REFERENCES model_runs(run_id),
    portfolio_id    VARCHAR(64) NOT NULL,
    risk_factor     VARCHAR(64) NOT NULL,
    weight          DOUBLE PRECISION NOT NULL,
    notional        DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (run_id, portfolio_id, risk_factor)
);

CREATE TABLE IF NOT EXISTS risk_results (
    run_id              VARCHAR(64) NOT NULL REFERENCES model_runs(run_id),
    forecast_date       DATE NOT NULL,
    portfolio_id        VARCHAR(64) NOT NULL,
    model_id            VARCHAR(64) NOT NULL,
    confidence          DOUBLE PRECISION NOT NULL,
    horizon             INTEGER NOT NULL,
    var                 DOUBLE PRECISION NOT NULL,
    expected_shortfall  DOUBLE PRECISION,
    realized_return     DOUBLE PRECISION,
    exception_flag      BOOLEAN,
    training_window     INTEGER,
    data_version        VARCHAR(64),
    PRIMARY KEY (run_id, forecast_date, portfolio_id, model_id)
);
CREATE INDEX IF NOT EXISTS idx_risk_results_portfolio_model_date
    ON risk_results(portfolio_id, model_id, forecast_date);

CREATE TABLE IF NOT EXISTS backtest_results (
    run_id            VARCHAR(64) NOT NULL REFERENCES model_runs(run_id),
    forecast_date     DATE NOT NULL,
    model_id          VARCHAR(64) NOT NULL,
    var               DOUBLE PRECISION NOT NULL,
    realized_return   DOUBLE PRECISION,
    realized_loss     DOUBLE PRECISION,
    exception_flag    BOOLEAN NOT NULL,
    PRIMARY KEY (run_id, forecast_date, model_id)
);

CREATE TABLE IF NOT EXISTS stress_results (
    run_id               VARCHAR(64) NOT NULL REFERENCES model_runs(run_id),
    scenario_id          VARCHAR(64) NOT NULL,
    risk_factor          VARCHAR(64) NOT NULL,
    shock                DOUBLE PRECISION NOT NULL,
    mapped_return_shock  DOUBLE PRECISION,
    factor_contribution  DOUBLE PRECISION,
    portfolio_loss       DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (run_id, scenario_id, risk_factor)
);

CREATE TABLE IF NOT EXISTS risk_attribution (
    run_id                       VARCHAR(64) NOT NULL REFERENCES model_runs(run_id),
    risk_factor                  VARCHAR(64) NOT NULL,
    weight                       DOUBLE PRECISION,
    pct_of_portfolio_variance    DOUBLE PRECISION,
    component_volatility         DOUBLE PRECISION,
    PRIMARY KEY (run_id, risk_factor)
);

CREATE TABLE IF NOT EXISTS credit_predictions (
    run_id          VARCHAR(64) NOT NULL REFERENCES model_runs(run_id),
    row_id          INTEGER NOT NULL,
    model_id        VARCHAR(64) NOT NULL,
    pd              DOUBLE PRECISION NOT NULL,
    lgd             DOUBLE PRECISION NOT NULL,
    ead             DOUBLE PRECISION NOT NULL,
    expected_loss   DOUBLE PRECISION NOT NULL,
    default_flag    INTEGER,
    segment         VARCHAR(64),
    PRIMARY KEY (run_id, row_id)
);
CREATE INDEX IF NOT EXISTS idx_credit_predictions_segment ON credit_predictions(run_id, segment);

CREATE TABLE IF NOT EXISTS risk_limits (
    run_id          VARCHAR(64) NOT NULL REFERENCES model_runs(run_id),
    metric          VARCHAR(64) NOT NULL,
    value           DOUBLE PRECISION NOT NULL,
    limit_value     DOUBLE PRECISION NOT NULL,
    utilization     DOUBLE PRECISION NOT NULL,
    status          VARCHAR(32) NOT NULL,
    PRIMARY KEY (run_id, metric)
);

CREATE TABLE IF NOT EXISTS model_inventory (
    run_id              VARCHAR(64) NOT NULL REFERENCES model_runs(run_id),
    model_id            VARCHAR(64) NOT NULL,
    purpose             VARCHAR(256),
    target              VARCHAR(256),
    data                VARCHAR(128),
    training_period     VARCHAR(128),
    features            TEXT,
    assumptions         TEXT,
    limitations         TEXT,
    version             VARCHAR(32),
    validation_status   VARCHAR(32),
    PRIMARY KEY (run_id, model_id)
);
