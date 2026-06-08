-- ============================================================
-- Migration: 00002_create_enums
-- Purpose  : Shared domain enumerations used across tables
-- ============================================================

-- Severity levels used by tickets, clusters, deployments, and investigations
create type severity_level as enum ('critical', 'high', 'medium', 'low');

-- Lifecycle status for tickets, fix recommendations, and resolutions
create type item_status as enum ('open', 'in_progress', 'resolved', 'closed');

-- User roles within an organisation (mirrors frontend TeamMember.role)
create type user_role as enum ('owner', 'admin', 'analyst', 'viewer');

-- Evidence types surfaced by the AI investigation engine
create type evidence_type as enum (
  'ticket_pattern',
  'deploy_correlation',
  'customer_impact',
  'similar_ticket'
);

-- Report types exported by the platform
create type report_type as enum ('executive_summary', 'cluster_detail', 'financial_impact', 'custom');

-- Deployment risk classification
create type deploy_risk as enum ('critical', 'high', 'medium', 'low');
