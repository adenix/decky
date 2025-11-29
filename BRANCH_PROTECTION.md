# Branch Protection Rules

This document describes the branch protection rules configured for the Decky repository.

## Protected Branches

### `main` Branch

The `main` branch is protected with the following rules:

## ✅ Required Status Checks

All PRs must pass these checks before merging:

1. **Test Python 3.10 on ubuntu-latest** - Unit and integration tests on Python 3.10
2. **Test Python 3.11 on ubuntu-latest** - Unit and integration tests on Python 3.11
3. **Test Python 3.12 on ubuntu-latest** - Unit and integration tests on Python 3.12
4. **Lint and Format Check** - Code formatting (Black, isort) and linting (flake8)
5. **Security Scanning** - Security analysis (Bandit, Safety, CodeQL)
6. **Pre-commit Hooks** - All pre-commit hooks must pass

### Status Check Configuration

- **Strict mode**: ✅ Enabled
  - Branches must be up-to-date with `main` before merging
  - Prevents merge conflicts

## 👥 Required Pull Request Reviews

- **Minimum approvals**: 1 reviewer
- **Code owner reviews**: ✅ Required
  - PRs must be approved by someone listed in `.github/CODEOWNERS`
- **Dismiss stale reviews**: ✅ Enabled
  - New commits dismiss previous approvals
  - Ensures reviewers see the latest code

## 🔒 Protection Rules

### Allowed Actions

- ✅ Regular commits to `main` (for admins/owners only)
- ✅ Merging approved PRs
- ✅ Creating tags for releases

### Blocked Actions

- ❌ **Force pushes** - Prevents `git push --force`
- ❌ **Branch deletion** - Can't delete `main` branch
- ❌ **Direct commits** (for non-admins) - Must use PRs

### Additional Requirements

- ✅ **Linear history** - Requires rebase or squash merging (no merge commits)
- ✅ **Conversation resolution** - All PR comments must be resolved before merge
- ❌ **Admin enforcement** - Admins can bypass (for emergency fixes)

## 🔄 Workflow

### For Contributors

1. **Fork the repository** (or create a branch if you have write access)
2. **Make your changes** and commit
3. **Open a Pull Request** to `main`
4. **Wait for CI checks** to complete (all must pass ✅)
5. **Request review** from a code owner
6. **Address review feedback** if any
7. **Resolve all conversations**
8. **Merge** once approved and all checks pass

### For Maintainers

1. **Review PR code** thoroughly
2. **Run locally if needed**: `gh pr checkout <number>`
3. **Approve** if changes look good
4. **Squash and merge** (recommended) or **Rebase and merge**
   - Avoid regular merge commits (linear history required)

## 🚨 Emergency Procedures

### If You Need to Bypass Protection

**Warning**: Only use in emergencies (critical security fixes, broken CI, etc.)

```bash
# Temporarily disable protection
gh api repos/adenix/decky/branches/main/protection -X DELETE

# Make your emergency fix
git push origin main

# Re-enable protection (run the setup script from BRANCH_PROTECTION.md)
```

**Better approach**: Create a PR and get it reviewed quickly, even for urgent fixes.

## 📊 Viewing Protection Status

### Via GitHub CLI

```bash
# View current protection rules
gh api repos/adenix/decky/branches/main/protection | jq

# View specific setting
gh api repos/adenix/decky/branches/main/protection | jq '.required_status_checks'
```

### Via GitHub Web UI

1. Go to: https://github.com/adenix/decky/settings/branches
2. View rules for `main` branch
3. See all protection settings

## 🔧 Modifying Protection Rules

### Add a New Required Status Check

```bash
# Add a new check (example: adding a performance test)
gh api repos/adenix/decky/branches/main/protection/required_status_checks/contexts -X POST --input - << 'EOF'
{
  "contexts": [
    "Test Python 3.10 on ubuntu-latest",
    "Test Python 3.11 on ubuntu-latest",
    "Test Python 3.12 on ubuntu-latest",
    "Lint and Format Check",
    "Security Scanning",
    "Pre-commit Hooks",
    "Performance Tests"  # NEW
  ]
}
EOF
```

### Change Review Requirements

```bash
# Require 2 approvals instead of 1
gh api repos/adenix/decky/branches/main/protection/required_pull_request_reviews -X PATCH --input - << 'EOF'
{
  "required_approving_review_count": 2,
  "dismiss_stale_reviews": true,
  "require_code_owner_reviews": true
}
EOF
```

### Enable Admin Enforcement

```bash
# Make admins follow the rules too
gh api repos/adenix/decky/branches/main/protection/enforce_admins -X POST
```

## 🎓 Best Practices

### For This Repository

1. **Always use PRs** - Even for small changes
2. **Write good commit messages** - Follow Conventional Commits
3. **Keep PRs small** - Easier to review and merge
4. **Update your branch** - Rebase on `main` before requesting review
5. **Run CI locally** - Use `make ci-local` before pushing

### Branch Strategy

- **`main`**: Protected, production-ready code
- **Feature branches**: `feature/add-new-action`, `fix/button-render`
- **Dependabot**: `dependabot/...` - Auto-created, auto-merged if checks pass

### Merge Strategies

**Recommended**: Squash and Merge
- Keeps `main` history clean
- Each PR becomes one commit
- Use for feature branches

**Alternative**: Rebase and Merge
- Preserves individual commits
- Use when commits are well-crafted
- Good for small, atomic PRs

**Avoid**: Regular Merge
- Creates merge commits
- Makes history messy
- Blocked by linear history requirement

## 📝 Summary

Branch protection ensures:

- ✅ All code is tested before merging
- ✅ All code is reviewed by a human
- ✅ No accidental deletions or force pushes
- ✅ Clean, linear git history
- ✅ All conversations are resolved before merge

This protects your `main` branch from bugs and maintains code quality! 🛡️

## 🔗 Resources

- [GitHub Branch Protection Documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [Status Checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks)
- [Required Reviews](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/about-pull-request-reviews)

