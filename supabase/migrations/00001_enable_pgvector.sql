-- ============================================================
-- Migration: 00001_enable_pgvector
-- Purpose  : Enable pgvector extension for ticket embeddings
-- ============================================================

create extension if not exists vector with schema extensions;
