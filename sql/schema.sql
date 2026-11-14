DROP TABLE IF EXISTS current_policy;
DROP TABLE IF EXISTS lead_time_history;
DROP TABLE IF EXISTS demand_history;
DROP TABLE IF EXISTS parts;

CREATE TABLE parts (
    part_id TEXT PRIMARY KEY,
    part_name TEXT NOT NULL,
    category TEXT NOT NULL,
    ved_class TEXT NOT NULL CHECK (ved_class IN ('V', 'E', 'D')),
    unit_cost REAL NOT NULL CHECK (unit_cost > 0),
    supplier_id TEXT NOT NULL,
    true_archetype TEXT NOT NULL,
    special_pattern TEXT NOT NULL
);

CREATE TABLE demand_history (
    date TEXT NOT NULL,
    part_id TEXT NOT NULL,
    demand_qty INTEGER NOT NULL CHECK (demand_qty >= 0),
    is_backtest INTEGER NOT NULL CHECK (is_backtest IN (0, 1)),
    PRIMARY KEY (date, part_id),
    FOREIGN KEY (part_id) REFERENCES parts(part_id)
);

CREATE TABLE lead_time_history (
    shipment_id TEXT PRIMARY KEY,
    part_id TEXT NOT NULL,
    supplier_id TEXT NOT NULL,
    order_date TEXT NOT NULL,
    lead_time_days INTEGER NOT NULL CHECK (lead_time_days > 0),
    FOREIGN KEY (part_id) REFERENCES parts(part_id)
);

CREATE TABLE current_policy (
    part_id TEXT PRIMARY KEY,
    min_stock INTEGER NOT NULL,
    max_stock INTEGER NOT NULL,
    initial_stock INTEGER NOT NULL,
    calibration_monthly_mean REAL NOT NULL,
    FOREIGN KEY (part_id) REFERENCES parts(part_id)
);

CREATE INDEX idx_demand_part_bt ON demand_history(part_id, is_backtest);
CREATE INDEX idx_lt_part ON lead_time_history(part_id);
