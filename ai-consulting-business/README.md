# AI CONSULTING BUSINESS - CUSTOMER ACQUISITION SYSTEM
## Complete Framework for Riordan Butler's Home Services AI Consulting

---

## OVERVIEW

This is your complete customer acquisition system for AI consulting targeting home services operators ($250K-$2M revenue).

**What's included:**
- 5-stage business model diagnostic framework
- Adaptive messaging templates (context-driven, not rigid scripts)
- Objection handling framework with Chris Voss tactical empathy
- Qualification criteria system with scoring
- 20 content post idea seeds (not finished posts)
- Client pipeline tracking (YAML files)
- Customer acquisition agent prompt (Claude Desktop compatible)

---

## FILE STRUCTURE

```
/ai-consulting-business/
│
├── README.md (this file)
├── customer-acquisition-agent.md (main agent prompt for Claude)
│
├── /frameworks/
│   ├── 5-stage-business-model.md
│   ├── adaptive-messaging-framework.md
│   ├── adaptive-objection-handling.md
│   └── qualification-criteria.md
│
├── /content-strategy/
│   └── 20-content-ideas.md
│
├── /client-pipeline/
│   ├── active-leads.yaml
│   ├── declined-leads.yaml
│   └── nurture-list.yaml
│
└── /case-studies/ (future - add client results here)
```

---

## HOW TO USE IN CLAUDE DESKTOP

### Option 1: Load the Agent Prompt Directly

**When you need customer acquisition help:**

1. **Start new chat in Claude Desktop**

2. **Copy-paste the agent prompt:**
   - File: `customer-acquisition-agent.md`
   - Or use this shorter invocation:

   ```
   Load my Customer Acquisition Agent for AI Consulting.

   Agent prompt location:
   C:\Users\riord\ai-consulting-business\customer-acquisition-agent.md

   Also reference:
   - Learning patterns: C:\Users\riord\ares-master-control-program\riord_learning_patterns.md
   - Frameworks: C:\Users\riord\ai-consulting-business\frameworks\

   I need help with: [describe your task]
   ```

3. **Claude will load the agent and help with:**
   - Qualifying leads
   - Crafting adaptive outreach
   - Prepping for discovery calls
   - Handling objections
   - Writing content
   - Tracking pipeline

### Option 2: Quick Task-Specific Help

**If you just need quick help without loading full agent:**

**For Lead Qualification:**
```
I need to qualify a lead for my AI consulting business.

Reference:
C:\Users\riord\ai-consulting-business\frameworks\qualification-criteria.md

Lead info: [paste their message or what you know]
```

**For Objection Handling:**
```
Need help handling this objection: "[objection]"

Context:
- Business: [name, stage, revenue]
- Discovery call insights: [what you learned]

Reference:
C:\Users\riord\ai-consulting-business\frameworks\adaptive-objection-handling.md
```

**For Discovery Call Prep:**
```
Discovery call tomorrow with [business name].

What I know:
- Revenue: $X
- Team: X staff
- Pain: [what they mentioned]

Reference:
C:\Users\riord\ai-consulting-business\frameworks\adaptive-messaging-framework.md (Discovery Call Prep section)

Help me prepare tactical empathy questions and anticipated objections.
```

**For Content Creation:**
```
Need to post this week. What did I actually work on?

[Describe your week's work]

Reference:
C:\Users\riord\ai-consulting-business\content-strategy\20-content-ideas.md

Which seed should I use and how do I adapt it?
```

### Option 3: Direct Framework Reference

**Just need to check a specific framework:**

- **"What stage is this client?"**
  → Read `frameworks/5-stage-business-model.md`

- **"How do I handle 'too expensive' objection?"**
  → Read `frameworks/adaptive-objection-handling.md` → Objection 1

- **"What's the qualification scorecard?"**
  → Read `frameworks/qualification-criteria.md` → Quick Qualification Scorecard

- **"How do I write a warm outreach message?"**
  → Read `frameworks/adaptive-messaging-framework.md` → Outreach Framework 1

---

## QUICK START EXAMPLES

### Example 1: New Lead from LinkedIn DM

**Your Prompt:**
```
New lead from LinkedIn DM:

"Hey Rio, saw your post about AI for home services. I run a plumbing business, about $500K/year with 10 staff. Drowning in admin work and missing calls. Interested to chat?"

Help me:
1. Qualify this lead (score it)
2. Draft a response

Reference my customer acquisition agent:
C:\Users\riord\ai-consulting-business\customer-acquisition-agent.md
```

**Claude Will:**
- Score the lead using qualification criteria
- Identify stage (likely Stage 2)
- Draft adaptive response in your voice
- Suggest next steps (discovery call, qualifying questions, etc.)

### Example 2: Preparing for Discovery Call

**Your Prompt:**
```
Discovery call tomorrow:

Business: ABC Electrical
Revenue: $650K
Team: 12 staff (3 crews)
Owner: Works 75 hrs/week
Current tools: ServiceM8, Xero
Pain mentioned: "Can't keep up with quotes, things fall through cracks"

Load customer acquisition agent and prep me for this call.

Agent: C:\Users\riord\ai-consulting-business\customer-acquisition-agent.md
```

**Claude Will:**
- Validate stage (Stage 2 solid)
- Provide tactical empathy questions (Chris Voss style)
- Anticipate objections and prepare reframes
- Set success criteria for the call

### Example 3: Handling "Let Me Think About It"

**Your Prompt:**
```
Just finished discovery call. They said "let me think about it."

Context:
- Stage 2 business, $480K revenue, 9 staff
- Clear pain: losing $5K/month in missed leads
- Budget: hesitated at $5K price tag
- Uses ServiceM8, tech-capable

What's the real objection and how do I respond?

Reference: C:\Users\riord\ai-consulting-business\frameworks\adaptive-objection-handling.md
```

**Claude Will:**
- Identify likely real objection (probably ROI concern or needs partner approval)
- Provide calibrated questions to uncover truth
- Draft response in your voice
- Suggest next steps

### Example 4: Weekly Content Creation

**Your Prompt:**
```
Need to post this week.

What I actually worked on:
- Implemented lead capture system for new client
- Tested 3 AI phone answering tools (2 were trash, 1 was decent)
- Had discovery call with prospect who thought AI would replace his whole team

Which content seed should I use and how do I adapt it?

Reference: C:\Users\riord\ai-consulting-business\content-strategy\20-content-ideas.md
```

**Claude Will:**
- Suggest 2-3 seed ideas that match your actual work
- Adapt the seed with specific variables from your week
- Write draft in your voice (direct, anti-hype, proof-based)
- Suggest hook angles

---

## UPDATING PIPELINE FILES

**After each lead interaction, update the appropriate YAML file:**

### Adding to Active Leads

**File:** `client-pipeline/active-leads.yaml`

**When:** Lead is qualified (10+ score), discovery scheduled/completed, proposal sent

**How:**
1. Open `active-leads.yaml`
2. Copy the template at the top
3. Fill in:
   - Business info (name, contact, revenue, team)
   - Qualification score and stage
   - Primary pain and estimated ROI
   - Pipeline stage (contacted, discovery_scheduled, etc.)
   - Next action + date
   - Relationship strength
4. Save file

**Tip:** You can ask Claude to generate the YAML entry for you:

```
Add this lead to my active pipeline:

Business: ABC Plumbing
Contact: John Smith, +61 400 123 456
Revenue: $450K, 8 staff
Pain: Spending 15 hrs/week on admin
Score: 16/18
Discovery call: Tomorrow

Generate YAML entry for: C:\Users\riord\ai-consulting-business\client-pipeline\active-leads.yaml
```

### Adding to Declined Leads

**File:** `client-pipeline/declined-leads.yaml`

**When:** Lead is disqualified (Stage 1, wrong problem, budget misalignment, etc.)

**Why Track:**
- Pattern recognition (if declining 80% for Stage 1, fix targeting)
- Future reconnection (they might be ready in 6 months)
- Reputation (declining gracefully = they remember you)

### Adding to Nurture List

**File:** `client-pipeline/nurture-list.yaml`

**When:** Lead is borderline (6-9 score), right profile but wrong timing

**Set:**
- Touchpoint frequency (monthly, quarterly, milestone-based)
- Next touchpoint date
- What you'll send (content, check-in, milestone congrats)

---

## FRAMEWORK QUICK REFERENCE

### When to Use Each Framework:

| Task | Framework File | Section |
|------|----------------|---------|
| Identify client stage | `5-stage-business-model.md` | Stage definitions + diagnostic questions |
| Price implementation | `5-stage-business-model.md` | Pricing guide by stage |
| Write outreach message | `adaptive-messaging-framework.md` | Outreach Framework 1 or 2 |
| Prep discovery call | `adaptive-messaging-framework.md` | Discovery Call Prep Framework |
| Handle objection | `adaptive-objection-handling.md` | Find the specific objection (1-7) |
| Qualify lead | `qualification-criteria.md` | Quick scorecard + decision tree |
| Decline gracefully | `qualification-criteria.md` | Graceful decline templates |
| Get content ideas | `20-content-ideas.md` | Pick seed that matches your week |

---

## INTEGRATION WITH LEARNING PATTERNS

**The system adapts to your communication style automatically.**

**Reference file:** `C:\Users\riord\ares-master-control-program\riord_learning_patterns.md`

**What this means:**
- Responses will be direct and concise (no fluff)
- You'll get 2-3 clear options (not open-ended questions)
- Teaching only when needed (if you've mastered a concept, it won't re-teach)
- ADHD-aware (flags shiny object risks, maintains focus)
- Uses your voice (direct, proof-based, anti-hype)

**As you use the system:**
- `riord_learning_patterns.md` will be updated after sessions
- `communication_effectiveness_log.yaml` tracks what works/fails
- Future responses adapt based on this learning

---

## BEST PRACTICES

### 1. Always Qualify Before Discovery Call
- Use the scorecard (0-18 points)
- Don't waste time on Stage 1 or obvious misfits
- Decline gracefully and provide value

### 2. Adapt, Don't Copy-Paste
- Templates are FRAMEWORKS, not scripts
- Customize based on:
  - Relationship strength
  - Business stage
  - Discovered pain points
  - Your proof points (Ki Landscapes, Asah Homes)

### 3. Track Everything in YAML Files
- Active leads → track next actions
- Declined leads → pattern recognition
- Nurture leads → future reconnection

**Why:** You'll forget context, YAML files don't lie

### 4. Reference Your Own Proof
- Ki Landscapes: Lead capture, route optimization, time savings
- Asah Homes: Built using these exact systems from day one
- Beta clients: Real results (when you have them)

**Don't:** Make unfounded claims or cite generic stats

### 5. Trust the Frameworks
- You built these based on proven sales methodologies
- Chris Voss tactical empathy works
- 5-stage model prevents selling wrong solutions
- Qualification criteria saves time

### 6. Update Learning Patterns
- After big wins or failures, update `riord_learning_patterns.md`
- Track what messaging works (effective strategies)
- Track what bombs (ineffective strategies)

**System gets smarter over time**

---

## TROUBLESHOOTING

### "Claude isn't using my frameworks"

**Fix:** Explicitly reference the framework file path in your prompt:

```
Reference this framework:
C:\Users\riord\ai-consulting-business\frameworks\[framework-name].md

[Your task]
```

### "Responses are too generic"

**Fix:** Provide more context:
- What stage is the client?
- What pain did they mention?
- What's the relationship strength?
- What do you know about their budget?

**More context = More adaptive response**

### "Claude is over-teaching me"

**Fix:** Remind it to check learning patterns:

```
Check my mastery level in:
C:\Users\riord\ares-master-control-program\riord_learning_patterns.md

I've already mastered [concept], don't re-teach it.
```

### "I need this faster"

**Fix:** Use direct framework reference instead of loading full agent:

```
Quick help: Read section X of [framework file] and apply to [situation].
```

---

## ADVANCED USAGE

### Multi-Lead Batch Processing

**Process multiple leads at once:**

```
Qualify these 3 leads (use scorecard):

Lead 1: [details]
Lead 2: [details]
Lead 3: [details]

Reference: C:\Users\riord\ai-consulting-business\frameworks\qualification-criteria.md

For each:
- Score (0-18)
- Recommendation (accept/decline/nurture)
- Next action
```

### Discovery Call Debrief + Next Steps

**After a discovery call:**

```
Discovery call debrief:

Business: [name]
Stage: [X]
Pain discovered: [specific pain points]
Objections raised: [list]
Their budget signal: [what they said]
My read on fit: [your gut feeling]

What's my next move?

Reference customer acquisition agent:
C:\Users\riord\ai-consulting-business\customer-acquisition-agent.md
```

### Content Calendar Planning

**Plan a month of content:**

```
Plan 4 posts for next month based on my actual work.

My focus areas this month:
- [Client implementation 1]
- [Client implementation 2]
- [Tool testing / research]
- [Discovery call insights]

Reference: C:\Users\riord\ai-consulting-business\content-strategy\20-content-ideas.md

For each week, suggest:
- Which seed to use
- How to adapt it
- Hook angle
```

---

## MAINTENANCE

### Monthly Reviews

**Check pipeline health:**
- How many leads in each stage?
- What's average qualification score of active leads?
- What's most common decline reason?
- Are you nurturing the right leads?

**Update frameworks:**
- If a new objection emerges repeatedly, add it to objection-handling.md
- If a messaging approach works especially well, document it
- If qualification criteria miss something, refine scorecard

### Quarterly Reviews

**Pattern recognition:**
- What's working in outreach? (check active leads → relationship_strength)
- What's working in discovery? (check close rate)
- Where are leads coming from? (referrals, content, cold, etc.)
- What stage clients are most profitable?

**Update learning patterns:**
- Add new mastered concepts
- Remove outdated communication preferences
- Update business context (new clients, new proof points)

---

## GETTING STARTED CHECKLIST

**First Time Setup:**

- [ ] Read this README fully
- [ ] Skim all framework files to understand what's available
- [ ] Test the customer acquisition agent with a real lead (or made-up one)
- [ ] Practice with one content seed
- [ ] Set up YAML tracking habit (update after each lead interaction)

**Before Each Discovery Call:**

- [ ] Read relevant section of `5-stage-business-model.md` for their stage
- [ ] Prep tactical empathy questions from `adaptive-messaging-framework.md`
- [ ] Review likely objections from `adaptive-objection-handling.md`
- [ ] Have qualification scorecard handy

**After Each Lead Interaction:**

- [ ] Update appropriate YAML file (active, declined, nurture)
- [ ] Note what worked/failed in approach
- [ ] If big win or failure, update learning patterns

**Weekly:**

- [ ] Create 1-2 content posts using `20-content-ideas.md` seeds
- [ ] Review active leads → follow up on next actions
- [ ] Check nurture list → any touchpoints due?

---

## SUPPORT

**If you need help with the system itself:**

1. **Check this README first** - Most questions answered here

2. **Ask Claude directly:**
   ```
   I'm having trouble with [X] in my customer acquisition system.

   System location: C:\Users\riord\ai-consulting-business\
   Issue: [describe problem]

   Reference the README and help me troubleshoot.
   ```

3. **Review learning patterns:**
   - Maybe the system is adapting in a way you don't want
   - Update preferences in `riord_learning_patterns.md`

4. **Update frameworks:**
   - If a framework isn't working, revise it
   - These are living documents, not gospel

---

## VERSION HISTORY

**v1.0 (2025-10-23):**
- Initial build with all core frameworks
- 5-stage business model diagnostic
- Adaptive messaging templates
- Objection handling with Chris Voss tactics
- Qualification criteria with scoring
- 20 content post idea seeds
- Client pipeline tracking (YAML)
- Customer acquisition agent prompt
- Integration with riord_learning_patterns.md
- Claude Desktop compatible

**Future Enhancements:**
- Case studies folder (add client results as they come)
- Proposal templates (when you have repeatable implementations)
- Pricing calculator (ROI estimator for discovery calls)
- Automated pipeline reminders (check-in on stale leads)

---

## FINAL NOTES

**This system is designed to:**
- Save you time (no reinventing outreach messages)
- Improve close rate (better qualification, objection handling)
- Build knowledge base (track what works, learn patterns)
- Scale with you (frameworks grow as business grows)

**This system is NOT:**
- Rigid scripts (adapt to context always)
- Set-and-forget (update with learnings)
- Replacement for judgment (use your gut + frameworks)

**Use it actively, update it regularly, trust the process.**

**Now go acquire customers for your AI consulting business.**

---

**AI CONSULTING BUSINESS - CUSTOMER ACQUISITION SYSTEM**
**Built for Riordan Butler**
**Version 1.0 - Updated: 2025-10-23**
