# LinkedIn Integration Setup Guide

This guide explains how to use the LinkedIn posting capability in your AI Employee (Silver Tier).

## Overview

The LinkedIn manager enables your AI Employee to draft professional posts for your business, with human approval before posting. This satisfies the Silver Tier requirement to "Automatically Post on LinkedIn about business."

**Important:** Due to LinkedIn API complexity, this implementation uses "Mock Mode" where posts are queued to a file for manual posting. This provides the same workflow benefits while avoiding complex OAuth2 setup.

## How It Works

### Workflow

```
1. AI drafts LinkedIn post based on business achievements
   ↓
2. Post saved to /Pending_Approval with action: linkedin_post
   ↓
3. Human reviews and approves (moves to /Approved)
   ↓
4. approval_handler.py queues post to LINKEDIN_QUEUE.md
   ↓
5. Human manually posts to LinkedIn
   ↓
6. File moves to /Done, action logged
```

## Setup

### Prerequisites

- Approval handler already configured
- LinkedIn account for your business

### No Additional Installation Required

The LinkedIn manager uses only Python standard library. No external dependencies needed.

## Usage

### Step 1: Start the Approval Handler

```bash
cd AI_Employee_Vault
python approval_handler.py
```

### Step 2: AI Creates Post Draft

When the AI identifies a business achievement worth sharing, it will:
1. Draft a professional LinkedIn post
2. Save to `/Pending_Approval/APPROVAL_LinkedIn_[Topic]_[Date].md`
3. Wait for your approval

### Step 3: Review and Approve

Check `/Pending_Approval` for LinkedIn post drafts:

```bash
ls -la AI_Employee_Vault/Pending_Approval/
```

Review the post content. If approved:

```bash
mv AI_Employee_Vault/Pending_Approval/APPROVAL_LinkedIn_Topic_20260216.md AI_Employee_Vault/Approved/
```

### Step 4: Check the Queue

The approval handler will automatically queue the post:

```bash
cat AI_Employee_Vault/LINKEDIN_QUEUE.md
```

### Step 5: Post to LinkedIn

1. Open the `LINKEDIN_QUEUE.md` file
2. Find the queued post
3. Copy the content
4. Go to https://www.linkedin.com
5. Click "Start a post"
6. Paste the content
7. Click "Post"
8. Mark the entry as posted in the queue file

## Post Guidelines

The AI follows these guidelines (defined in `/Agent_Skills/social_media.md`):

### Content Types
- **Achievement Posts:** Milestones, completed projects, client wins
- **Insight Posts:** Industry knowledge, lessons learned
- **Value Posts:** Actionable tips, frameworks, resources
- **Engagement Posts:** Questions, discussions, community building

### Formatting
- Hook in first line (grabs attention)
- Short paragraphs (2-3 lines max)
- Bullet points for readability
- 1-3 emojis sparingly
- Call-to-action or question at end
- 3-5 relevant hashtags

### Length
- Optimal: 150-300 words
- Maximum: 500 words
- First 2 lines are critical (visible before "see more")

## Testing

A test post is included in `/Pending_Approval/TEST_LinkedIn_Post.md`.

To test the workflow:

1. **Start approval handler:**
   ```bash
   python approval_handler.py
   ```

2. **Approve the test post:**
   ```bash
   mv AI_Employee_Vault/Pending_Approval/TEST_LinkedIn_Post.md AI_Employee_Vault/Approved/
   ```

3. **Check the queue:**
   ```bash
   cat AI_Employee_Vault/LINKEDIN_QUEUE.md
   ```

4. **Verify logging:**
   ```bash
   cat AI_Employee_Vault/Logs/actions.log
   ```

You should see:
- Post queued to LINKEDIN_QUEUE.md
- Action logged with SUCCESS status
- File moved to /Done

## Example Post

Here's what a typical AI-generated LinkedIn post looks like:

```markdown
🚀 Excited to share a major milestone!

We've successfully automated 85% of our routine business tasks using AI.

Key results:
✅ 24/7 monitoring without burnout
✅ Complete transparency and audit trails
✅ Human oversight for all sensitive actions

The future isn't AI replacing humans—it's AI empowering humans.

Curious about implementing AI in your business? Let's connect.

#AI #Automation #BusinessInnovation #ProductivityHacks
```

## Queue Management

### Check Queue Status

```bash
python linkedin_manager.py
```

This shows:
- Total posts queued
- Posts marked as posted
- Posts pending

### Mark Posts as Posted

After manually posting to LinkedIn, edit `LINKEDIN_QUEUE.md`:

Change:
```
**Posted:** [ ] Yes  [ ] No
```

To:
```
**Posted:** [x] Yes  [ ] No
**Posted Date:** 2026-02-16
**Post URL:** https://linkedin.com/posts/...
```

## Approval File Format

### Required Frontmatter

```yaml
---
action: linkedin_post
created: 2026-02-16T18:15:00Z
status: pending_approval
priority: normal
category: achievement  # or: insight, value, engagement, bts
target_audience: potential_clients  # or: peers, recruiters, general
---
```

### Post Content

Write the complete LinkedIn post after the frontmatter:

```markdown
🚀 Your engaging hook here...

[Post content with formatting]

#Hashtag1 #Hashtag2 #Hashtag3
```

## Troubleshooting

### Posts not appearing in queue

**Check:**
- Is approval_handler.py running?
- Did you move file to /Approved (not just /Pending_Approval)?
- Check logs: `cat AI_Employee_Vault/Logs/ApprovalHandler.log`

### LinkedIn manager not found

**Solution:**
```bash
cd AI_Employee_Vault
python -c "from linkedin_manager import LinkedInManager; print('OK')"
```

If error, ensure `linkedin_manager.py` exists in the vault.

### Queue file not created

**Solution:**
The queue file is created automatically on first post. If missing:
```bash
touch AI_Employee_Vault/LINKEDIN_QUEUE.md
```

## Future Enhancement: API Mode

Currently using Mock Mode (manual posting). To upgrade to API mode:

### Requirements
1. Create LinkedIn Developer App at https://www.linkedin.com/developers/
2. Get OAuth2 credentials
3. Implement OAuth2 flow in `linkedin_manager.py`
4. Use LinkedIn Share API

### Implementation
Update `linkedin_manager.py`:
```python
manager = LinkedInManager(vault_path, mode="api")
```

Then implement the `_post_via_api()` method with LinkedIn API calls.

## Best Practices

### Content Strategy
- Post 2-3 times per week
- Mix content types (achievement, insight, value)
- Engage with comments promptly
- Track performance metrics

### Approval Workflow
- Review posts within 24 hours
- Provide feedback on rejected posts
- Update social_media.md with learnings

### Queue Management
- Post queued items within 48 hours
- Mark posts as posted immediately
- Archive old queue entries monthly

## Integration with Other Skills

### Planning Skill
For complex posts, the AI may create a plan first:
- `/Plans/PLAN_LinkedIn_Campaign_Q1.md`
- Documents content strategy
- Links to individual post approvals

### Dashboard Updates
LinkedIn activity appears on Dashboard:
- Posts queued
- Posts approved/rejected
- Engagement metrics (manual entry)

## Security Notes

### What's Queued
- Post content only (text)
- No credentials or tokens
- No personal information

### What's Logged
- Action type (linkedin_post)
- Timestamp
- Status (SUCCESS/FAILED)
- Post preview (first 50 chars)

### What's NOT Stored
- LinkedIn credentials
- API tokens
- Session cookies

## FAQ

**Q: Why not use LinkedIn API directly?**
A: LinkedIn API requires OAuth2 app registration, which is complex for personal use. Mock Mode provides the same workflow benefits without the complexity.

**Q: Can I automate the manual posting step?**
A: Yes, with LinkedIn API implementation. See "Future Enhancement: API Mode" above.

**Q: How do I track post performance?**
A: Manually add metrics to the queue file after posting, or use LinkedIn Analytics.

**Q: Can I schedule posts?**
A: Not in Mock Mode. With API Mode, you could implement scheduling.

**Q: What if I want to post to other platforms?**
A: Extend the social_media.md skill and create similar managers for Twitter, Facebook, etc.

---

**Status:** Ready to use (Mock Mode)
**Next Step:** Test with TEST_LinkedIn_Post.md
**Upgrade Path:** Implement API Mode for full automation
