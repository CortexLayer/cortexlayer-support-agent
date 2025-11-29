# Cron Jobs

## Daily Billing Jobs

### 1. Overage Billing (Daily)
Runs daily.  
Checks monthly usage and:
- Bills soft cap overage (limit + 20%)
- Disables client after hard cap (limit + 50%)

### 2. Grace Period Enforcement (Daily)
Disables clients who have been in GRACE_PERIOD for more than 7 days.

### How to Run (Development)
Call `run_daily_jobs()` manually from Python shell.

### Production Setup
Use:
- GitHub Actions
- AWS Cron / ECS Scheduled Task
- Railway cron worker
