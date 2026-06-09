# VLM Figure Verification Protocol (Optional)

**Status**: v3.3
**Used by**: `visualization_agent`
**Requires**: Multimodal LLM with vision capability (e.g., Claude with vision, GPT-4V)

---

## Purpose

After the visualization_agent generates a figure, an optional verification loop uses a vision-capable LLM to check the rendered figure against the paper's data and APA 7.0 standards. This catches issues invisible in code review: truncated labels, overlapping text, incorrect data rendering, misleading scales.

Inspired by PaperOrchestra's Plotting Agent (Song et al., 2026), which uses a "VLM critic" in a closed-loop refinement system.

---

## When to use

- **Recommended**: When figures contain complex data (multi-panel, many categories, statistical plots)
- **Optional**: For simple figures (single bar chart, basic line plot)
- **Required**: When the pipeline is in `final-check` mode (Stage 4.5+)
- **Skip**: When no multimodal capability is available (graceful degradation)

---

## Verification Checklist

The VLM receives the rendered figure image and the source data, then checks:

### Data Accuracy
1. Do the plotted values visually match the source data? (e.g., a bar labeled "45%" should be approximately 45% of the axis range)
2. Are all data series present? (no missing categories or groups)
3. Do error bars / confidence intervals appear correct in scale?

### APA 7.0 Compliance
4. Are both axes labeled with descriptive text and units?
5. Is the legend present and readable (for multi-series)?
6. Is the figure title in the correct format (bold label + italic title)?
7. Are fonts readable at publication size (no text < 8pt)?

### Visual Quality
8. Is any text truncated, overlapping, or cut off at figure edges?
9. Are colors distinguishable (no two series with visually identical colors)?
10. Is the figure free of chart junk (3D effects, unnecessary gridlines)?

---

## Verification Loop

```
Step 1: visualization_agent generates figure code
Step 2: Execute code to render figure image
Step 3: Send figure image + source data + checklist to VLM
Step 4: VLM returns pass/fail for each checklist item
Step 5: If any FAIL:
  - VLM describes the specific issue
  - visualization_agent modifies code to fix
  - Return to Step 2 (max 2 iterations)
Step 6: If all PASS or max iterations reached:
  - Attach verification result to Figure Package
  - Any remaining issues noted in figure caption Note
```

**Max iterations**: 2 refinement cycles (3 total renders). If issues persist after 2 fixes, flag for user review rather than continuing the loop.

---

## Output Addition to Figure Package

When VLM verification is run, the Figure Package (from visualization_agent) includes:

```markdown
### VLM Verification
- **Status**: PASS / PASS_WITH_NOTES / NEEDS_REVIEW / SKIPPED
- **Iterations**: [N] (1 = passed first time, N/A if SKIPPED)
- **Issues found**: [list of issues, if any]
- **Issues fixed**: [list of fixes applied]
- **Remaining issues**: [issues that could not be auto-fixed, if any]
```

---

## References

- Song, Y. et al. (2026). PaperOrchestra. *arXiv:2604.05018*. — Section 4 Step 2 (Plotting Agent with VLM critic).
- Zhu, D. et al. (2026). PaperBanana: Automating academic illustration for AI scientists. *arXiv:2601.23265*. — Closed-loop VLM refinement system.
