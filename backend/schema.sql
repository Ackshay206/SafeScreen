-- ============================================
-- SafeScreen — Supabase SQL Schema
-- Run this in the Supabase SQL Editor (one time)
-- ============================================

create extension if not exists "uuid-ossp";

-- ---- Profiles ----
create table if not exists profiles (
  id               uuid primary key default uuid_generate_v4(),
  name             text not null,
  age              integer not null check (age >= 1 and age <= 120),
  sensitivities    jsonb not null default '{}'::jsonb,
  calming_strategy text not null default '',
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);

-- ---- Movies ----
create table if not exists movies (
  id                     uuid primary key default uuid_generate_v4(),
  title                  text not null,
  year                   integer not null,
  genre                  text[] not null default '{}',
  runtime_minutes        integer not null default 0,
  poster_url             text not null default '',
  synopsis               text not null default '',
  mpaa_rating            text not null default 'NR',
  transcript_file        text,
  transcript_content     text,
  overall_flags          jsonb not null default '{}'::jsonb,
  segments               jsonb not null default '[]'::jsonb,
  plain_language_summary text not null default '',
  analyzed_at            timestamptz
);

-- ---- Viewing Plans (for future use) ----
create table if not exists viewing_plans (
  id             uuid primary key default uuid_generate_v4(),
  profile_id     uuid not null references profiles(id) on delete cascade,
  movie_id       uuid not null references movies(id) on delete cascade,
  sessions       jsonb not null default '[]'::jsonb,
  total_sessions integer not null default 1,
  plan_summary   text not null default '',
  generated_at   timestamptz not null default now()
);

-- ---- Feedback (for future use) ----
create table if not exists feedback (
  id                      uuid primary key default uuid_generate_v4(),
  profile_id              uuid not null references profiles(id) on delete cascade,
  movie_id                uuid not null references movies(id) on delete cascade,
  plan_id                 uuid not null references viewing_plans(id) on delete cascade,
  strictness_rating       text not null check (strictness_rating in ('too_strict','about_right','too_loose')),
  child_seemed_distressed boolean not null default false,
  optional_note           text,
  submitted_at            timestamptz not null default now()
);

-- ---- RLS (open for hackathon MVP) ----
alter table profiles      enable row level security;
alter table movies        enable row level security;
alter table viewing_plans enable row level security;
alter table feedback      enable row level security;

create policy "Allow all on profiles"      on profiles      for all using (true) with check (true);
create policy "Allow all on movies"        on movies        for all using (true) with check (true);
create policy "Allow all on viewing_plans" on viewing_plans for all using (true) with check (true);
create policy "Allow all on feedback"      on feedback      for all using (true) with check (true);
