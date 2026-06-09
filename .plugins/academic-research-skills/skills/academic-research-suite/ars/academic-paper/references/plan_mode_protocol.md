# Plan Mode: Chapter-by-Chapter Guided Planning

Core principle: From the perspective of a senior doctoral advisor and disciplinary methodology expert, guide users to think through every part of their paper chapter by chapter. Instead of writing directly, use Socratic dialogue to help users clarify what they want to write.

```
User: "guide my paper" / "help me plan my paper"
     |
=== Step 0: RESEARCH READINESS CHECK ===
     |
     +-> [socratic_mentor_agent] -> Confirm what materials the user already has
         - "What research materials do you currently have? (literature, data, analysis results)"
         - "Is your research question finalized? Can you state it in one sentence?"
         -> If research foundation is lacking, recommend running deep-research (socratic mode) first
     |
=== Step 1: THESIS CRYSTALLIZATION ===
     |
     +-> [socratic_mentor_agent] -> Probe the core thesis
         - "What is your paper arguing?"
         - "How would someone who disagrees with you respond?"
         - "After reading your paper, what should the reader think differently about?"
         Extract [INSIGHT: thesis_statement]
     |
=== Step 2: CHAPTER-BY-CHAPTER NEGOTIATION ===
     |
     For each chapter (Introduction -> Literature -> Method -> Results -> Discussion -> Conclusion):
     |
     +-> [socratic_mentor_agent] -> Probe the purpose and content of each chapter
     |
     |   Introduction:
     |   - "What sense of urgency should the reader feel by the end of this chapter?"
     |   - "After reading the Introduction, what should the reader expect to see next?"
     |   - "What is your research gap? State it in one sentence."
     |
     |   Literature Review:
     |   - "How many stories are you telling? What is the relationship between them?"
     |   - "What conclusion should your literature review ultimately lead to?"
     |   - "Is there an important work you disagree with? Why?"
     |
     |   Methodology:
     |   - "If someone challenges your method, how would you respond?"
     |   - "Is there a simpler method that could also answer your question? Why didn't you choose it?"
     |   - "What is the biggest limitation of your method? How do you handle it?"
     |
     |   Results:
     |   - "What is your most important finding? State it in one sentence."
     |   - "Were there any unexpected results? How do you explain them?"
     |   - "Is there any evidence in your data that does not support your hypothesis?"
     |
     |   Discussion:
     |   - "How do your results dialogue with existing literature?"
     |   - "What is the one thing you most want the reader to remember?"
     |   - "What recommendations does your research have for practice/policy?"
     |
     |   Conclusion:
     |   - "If you could only leave one paragraph, what would you say?"
     |   - "What future research directions does your study open up?"
     |
     At least 2 rounds of dialogue per chapter
     After each chapter concludes, [socratic_mentor_agent] extracts a Chapter Summary
     |
     +-> [structure_architect_agent] -> Produce complete outline based on all Chapter Summaries
     |
=== Step 3: ARGUMENT STRESS TEST ===
     |
     +-> [socratic_mentor_agent + argument_builder_agent]
         -> Probe evidence and logic for each sub-argument
         -> "Where is the weakest point in this argument?"
         -> "If you reverse your argument, does it still hold?"
         -> Final output: Chapter Plan (with core argument, supporting evidence, expected word count per chapter)
     |
Output: Chapter Plan + INSIGHT Collection
-> User can then use full mode to produce the complete paper
-> Or use academic-paper-reviewer to review the Chapter Plan
```

## Plan Mode Activation Rules

Activate `plan` mode (Socratic chapter-by-chapter guidance) when the user's **intent** matches any of the following patterns, **regardless of language**. Detect meaning, not exact keywords.

**Intent signals** (any one is sufficient):
1. User wants to be guided or led through paper writing, not just given a finished paper
2. User asks for step-by-step or chapter-by-chapter planning
3. User expresses uncertainty about how to start or structure a paper
4. User is a first-time paper writer or explicitly says they are a beginner
5. User has research results but doesn't know how to turn them into a paper
6. User wants to think through each section before writing

**Default rule**: When intent is ambiguous between `plan` and `full`, **prefer `plan`** — it is safer to guide a user who needs help than to produce a paper they can't use. The user can always switch to `full` later.

**Example triggers** (illustrative, not exhaustive):
"guide my paper", "help me plan my paper", "I don't know how to start", 「引導我寫論文」「幫我規劃論文」, or equivalent in any language
