<#
.SYNOPSIS
  COMMIT standard — Steps 3-5 of the post-implementation workflow.

.DESCRIPTION
  Stages all changes, commits with the given message, and pushes to origin.
  Must be on a feat/* or fix/* branch (not main).
  Steps 1-2 (git pull main + new branch) are done at session start per CLAUDE.md.

.PARAMETER Message
  Conventional Commits message, e.g. "feat(scope): add xyz"

.PARAMETER Amend
  If set, amends the most recent commit instead of creating a new one.
  Use for subsequent changes on the same branch (one-commit-per-branch rule).

.EXAMPLE
  scripts/commit.ps1 -Message "feat(scope): add xyz"
  scripts/commit.ps1 -Amend
#>
param(
    [Parameter(Mandatory=$false)] [string]$Message = "",
    [switch]$Amend
)

$branch = git rev-parse --abbrev-ref HEAD 2>$null
if (-not ($branch -match '^(feat|fix)/')) {
    Write-Error "commit.ps1: must be on a feat/* or fix/* branch (current: '$branch'). Run 'git checkout -b feat/<slug>' first."
    exit 1
}

git add -A

if ($Amend) {
    git commit --amend --no-edit
} elseif ($Message) {
    git commit -m $Message
} else {
    Write-Error "commit.ps1: provide -Message 'feat(scope): description' or use -Amend for subsequent changes."
    exit 1
}

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

git push -u origin $branch
if ($LASTEXITCODE -eq 0) {
    Write-Host "Pushed $branch to origin." -ForegroundColor Green
}
