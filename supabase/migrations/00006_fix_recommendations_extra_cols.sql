-- ============================================================
-- Migration: 00006_fix_recommendations_extra_cols
-- Purpose  : Add missing columns to fix_recommendations that
--            the AI recommendation service writes but the
--            original schema did not include.
-- ============================================================

ALTER TABLE public.fix_recommendations
  ADD COLUMN IF NOT EXISTS priority                    text,
  ADD COLUMN IF NOT EXISTS engineering_effort          text,
  ADD COLUMN IF NOT EXISTS confidence_score            numeric(5,2),
  ADD COLUMN IF NOT EXISTS jira_title                  text,
  ADD COLUMN IF NOT EXISTS jira_description            text,
  ADD COLUMN IF NOT EXISTS jira_acceptance_criteria    text[],
  ADD COLUMN IF NOT EXISTS jira_severity               text;

comment on column public.fix_recommendations.priority               is 'AI-assigned priority: critical|high|medium|low';
comment on column public.fix_recommendations.engineering_effort     is 'Estimated effort: low|medium|high|very_high';
comment on column public.fix_recommendations.confidence_score       is 'LLM confidence (0-100%)';
comment on column public.fix_recommendations.jira_title             is 'Generated Jira ticket title';
comment on column public.fix_recommendations.jira_description       is 'Generated Jira ticket description (markdown)';
comment on column public.fix_recommendations.jira_acceptance_criteria is 'Generated Jira acceptance criteria (array of strings)';
comment on column public.fix_recommendations.jira_severity          is 'Jira severity: blocker|critical|major|minor|trivial';
