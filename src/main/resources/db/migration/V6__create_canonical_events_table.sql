create table canonical_events (
                                  id uuid primary key,
                                  created_at timestamp with time zone not null,
                                  updated_at timestamp with time zone not null,
                                  created_by varchar(255),
                                  updated_by varchar(255),
                                  agent_key varchar(64) not null,
                                  message_timestamp timestamp with time zone not null,
                                  environment varchar(32) not null,
                                  data jsonb not null
);

create index ix_canonical_events_agent_key on canonical_events (agent_key);
create index ix_canonical_events_message_timestamp on canonical_events (message_timestamp);