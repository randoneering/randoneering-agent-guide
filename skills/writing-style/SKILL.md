---
name: writing-style
description: "Justin's personal blog writing style for Hugo site content. Triggers: blog posts, weekly updates, technical tutorials. Covers conversational tone, honest reflection, technical accessibility, and storytelling approach."
---

# Justin's Writing Style Guide

Guidelines for writing blog posts and content that matches the established voice and style of this Hugo site.

## Core Voice Characteristics

### Personal and Conversational
- Write in first person ("I", "my")
- Talk directly to readers using "you"
- Share personal experiences, mistakes, and learning journeys
- Be honest about failures and challenges
- Use conversational asides and parentheticals
- Write like you're talking to a friend who's technical but not necessarily expert in this specific topic

### Honest and Self-Reflective
- Admit when you were wrong: "I was wrong about this"
- Share the journey, including missteps
- Don't pretend to know everything
- Acknowledge when something was harder than expected
- Give credit to others who helped (friends, community, Stack Overflow)

### Technically Accessible
- Explain concepts clearly without dumbing down
- Use technical terms but explain the "why" behind them
- Share actual code examples and configurations
- Reference documentation and sources with links or footnotes
- Balance technical depth with readability

## Tone and Language

### Casual but Informed
**Use these patterns:**
- "Seemed straightforward enough" (followed by complications)
- "Hold up..." or "Wait!" for interrupting your own flow
- "You might have noticed..."
- "Yeah, you can..." for confirming something
- "I will admit that..."
- Rhetorical questions followed by answers

**Examples:**
- "The problem is I actually went from Ubuntu 24.04 to NixOS because of how buggy it was!"
- "You know what would be really nice? Moving all my servers over..."
- "If you are paying attention, you might have noticed..."
- "Turns out I needed to grab roles..."

### Humor and Personality
- Self-deprecating humor: "I was dumb enough to jump to..."
- Playful spellings: "guh-nome (gnome)", "jobby job"
- Light sarcasm about tech frustrations
- Acknowledge absurdities in tech culture
- Use "honestly" when expressing genuine feelings

### Strong Opinions, Loosely Held
- Have clear preferences but explain reasoning
- Willing to change your mind when presented with evidence
- Acknowledge counterarguments
- Don't gatekeep or look down on different choices
- "For me, I..." rather than "You should..."

## Content Structure

### Opening Patterns

**The Context Set:**
Start with background or current situation
```markdown
After a failed upgrade to NixOS 24.11 and ultimately being annoyed
with my drive to always make things perfect, I went back to my
comfort zone.
```

**The Ask:**
Frame as a problem or request
```markdown
# The Ask

I was asked to do the following. First, I needed to run a backup
of specific databases...
```

**The Journey:**
Chronicle your path to a solution
```markdown
# NixOS Journey, Part 1

So, for those who have yet to go down this path, it would be
helpful to explain what NixOS is.
```

### Section Headers

Use headers to organize and provide navigation:
- Direct and descriptive
- Sometimes questions: "## Are you starting to get it yet?"
- Sometimes exclamations: "# I was wrong"
- Use subheadings to break up long sections
- Tool Shed, Planned Outcome, Stretch Goal, etc.

### Middle Content

**The Build:**
- Walk through your process step-by-step
- Explain decision points
- Share code snippets with context
- Call out variables and important details
- Show both what worked and what didn't

**Interruptions:**
- Break your own flow to clarify: "## Hold up, some variables!"
- Address reader questions proactively
- Provide warnings or tips inline

### Closing Patterns

**The Reflection:**
- What you learned
- What's next
- Acknowledgment of limitations
- "Here's to staying put until..."

**The Resource Share:**
- Link to GitHub repos
- Share full scripts
- Recommend tools or reading
- Provide actionable next steps

## Technical Writing Specifics

### Code and Configuration

**Always provide context:**
```markdown
Now that I have my desired variable in place for my server names
and database names, I went to work on the actual foreach loop
that would do the work.
```

**Explain gotchas:**
```markdown
You might have ALSO noticed I used pg_dumpall instead of pg_dump.
Interesting right? Turns out I needed to grab roles...
```

**Share the full picture:**
- Include both snippets and complete scripts
- Point to GitHub for full code
- Explain parameters and flags
- Warn about pitfalls: "I highly recommend... to AVOID putting a compression higher than 5"

### Citations and Sources

Use footnotes for references:
```markdown
[^1]: https://openai.com/index/chatgpt/
[^2]: https://www.example.com/article
```

Include sources at the end of articles, especially for:
- Technical documentation
- Research or claims
- Tools and projects mentioned
- Community resources

## Topic-Specific Patterns

### Weekly Posts
- Start with personal updates (fundraising, life events)
- Include distro/tech journey updates
- Share fediverse/FOSS recommendations
- Tool Shed section with brief tool highlights
- Mix of technical and personal

### Technical Tutorials
- Frame the problem first
- Show your solution journey
- Include full working code
- Acknowledge helpers and resources
- End with GitHub link or next steps

### Opinion Pieces
- Start with your position
- Acknowledge counterarguments
- Share personal reasoning
- Stay humble about being wrong
- Focus on "ethical usage" or practical implications

## What to Avoid

### Don't Use AI Buzzwords
- No "leverage", "synergy", "cutting-edge"
- No "seamlessly", "robust", "innovative"
- Just say what it actually does

### Don't Be Overly Formal
- Avoid academic/corporate tone
- No "moreover", "furthermore", "in conclusion"
- No "it is important to note that"
- No "in today's fast-paced world"

### Don't Hide Complexity
- Don't pretend things were easy if they weren't
- Don't skip the messy parts
- Don't oversell your solution
- Share both successes and failures

### Don't Gatekeep
- Don't shame "normies" (except good-natured Twitter jokes)
- Don't assume everyone knows what you know
- Do explain acronyms and terms
- Do acknowledge different skill levels

## Content Categories

### homelab/
Projects and infrastructure work
- Focus on practical implementation
- Share configs and setups
- Document problems and solutions
- Progress updates on ongoing projects

### databases/
Database administration and automation
- Step-by-step tutorials
- Full scripts with explanations
- Performance considerations
- Real-world problem solving

### nixos/
NixOS exploration and learning
- Journey documentation
- Config evolution
- Honest assessment of challenges
- Community learning

### random/
Opinions and broader tech topics
- Personal stance on tech trends
- Ethical considerations
- Philosophy of tool usage
- Community observations

### weekly/
Regular updates and news
- Personal life updates
- Current projects
- Tool recommendations
- Fediverse/FOSS advocacy
- Mixed technical and personal content

## Examples of Voice

### Good Opening:
"As the AI Chatbot Hype-Train started chugging along at the first announcement of OpenAI's ChatGPT in November of 2022, I will admit that I was an immediate skeptic."

### Good Explanation:
"What this allows the users to do is work within a declarative configuration. If you make a change to the configuration file and want the changes to take, you run `nixos-rebuild switch`."

### Good Problem Framing:
"My first problem was finding a way to pass a database hostname through and for each of those hostnames, go down the line of databases that needed to be backed up."

### Good Self-Reflection:
"I really do not enjoy jumping from distro to distro. It gets exhausting and is really time consuming. It takes me away from being able to work on my projects or even just use the laptop itself."

### Good Casual Aside:
"(except Debian, please do not make me hate myself more and tell me to go to Debian)"

## Quick Reference Checklist

Before publishing, verify:
- [ ] Written in first person with personal experience
- [ ] Conversational tone, not corporate or academic
- [ ] Technical concepts explained clearly
- [ ] Code examples with context and explanation
- [ ] Honest about challenges and mistakes
- [ ] Headers organize content logically
- [ ] Sources cited with footnotes or links
- [ ] No AI buzzwords or corporate speak
- [ ] Reflects actual learning journey
- [ ] Ends with practical takeaway or next steps

**Key principle:** Write like you're explaining to a friend over coffee, not presenting at a conference. Be technical, be honest, be yourself.

---

**Note:** This is about voice and style, not content requirements. The goal is authenticity and accessibility, not perfection.
