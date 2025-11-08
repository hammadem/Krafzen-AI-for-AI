#!/bin/bash
# Init Supabase (run after CLI install: npm i -g supabase)
echo "Initializing Supabase schema..."
# Link project: supabase link --project-ref your-project-id
supabase db push app/db/schema.sql
echo "Schema pushed! Validate with Teammate."
