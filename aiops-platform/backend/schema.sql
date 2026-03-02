-- Auto-generated from SQLAlchemy models (PostgreSQL dialect).
-- Re-generate with: python backend/scripts/export_schema.py

CREATE TABLE error_knowledge_base (
	id UUID NOT NULL, 
	fingerprint VARCHAR(64), 
	normalized_message TEXT NOT NULL, 
	raw_message TEXT NOT NULL, 
	error_type VARCHAR(100), 
	service VARCHAR(100), 
	api VARCHAR(255), 
	label VARCHAR(30), 
	severity VARCHAR(20), 
	solution TEXT, 
	auto_fix_script TEXT, 
	first_seen TIMESTAMP WITHOUT TIME ZONE, 
	last_seen TIMESTAMP WITHOUT TIME ZONE, 
	occurrence INTEGER, 
	confidence_score FLOAT, 
	PRIMARY KEY (id)
);

CREATE TABLE error_trace_map (
	id UUID NOT NULL, 
	trace_id VARCHAR(255) NOT NULL, 
	error_id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE TABLE incidents (
	id UUID NOT NULL, 
	fingerprint VARCHAR(64), 
	message TEXT NOT NULL, 
	error_type VARCHAR(50), 
	severity VARCHAR(20), 
	service VARCHAR(100), 
	api VARCHAR(255), 
	status VARCHAR(20), 
	assigned_to VARCHAR(100), 
	count INTEGER, 
	first_seen TIMESTAMP WITHOUT TIME ZONE, 
	last_seen TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE TABLE processed_log_events (
	id UUID NOT NULL, 
	event_id VARCHAR(255) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_error_knowledge_base_fingerprint ON error_knowledge_base (fingerprint);

CREATE UNIQUE INDEX ix_error_trace_map_trace_id ON error_trace_map (trace_id);
CREATE INDEX ix_error_trace_map_error_id ON error_trace_map (error_id);

CREATE INDEX ix_incidents_fingerprint ON incidents (fingerprint);

CREATE UNIQUE INDEX ix_processed_log_events_event_id ON processed_log_events (event_id);
