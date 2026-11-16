---
name: review-packet
description: "Writes the review packet for one of the user's code reviews in the crazyflie-behavior repo, to drafts/review-packet-<date>.md: the reading order by review tier, what changed in each file and its ADR, where it could be wrong (from the mistakes log), the facts it relies on, new log messages, new and changed tests, the findings, and explain-back questions. Use it before one of the user's code reviews, right after /project-review in the same work session so the packet carries its findings. It also works on a range no project review covered, and says so. Argument: a commit range (default: from the last reviewed commit in REVIEW.md's review log to main)."
---

# Review packet

The user reads the code at review points, as a pull request in PyCharm. A
findings list alone leaves that read starting cold: which file first, what
changed and why, what was checked and what wasn't. The packet answers those
before the first file is opened, and its explain-back questions show the
user whether they can defend the change.

It's apart from `/project-review` because the two run at different times: a
project review before every commit to the safety layer, the Crazyflie
adapter or the tick loop, and a packet only before one of the user's code
reviews, over everything since the last one. When `/project-review` ran
earlier in the same work session, the packet carries its findings.

## Arguments

`/review-packet [range]`: a commit range. Default: from the "Reviewed up to"
commit in the last filled row of `REVIEW.md`'s review log to `main`. Once
the `reviewed` branch exists it marks the same commit. If the two disagree,
stop and ask: one of them is wrong, and the range would be too.

Before a review, `REVIEW.md` ("My reviews") runs it on
`reviewed..review/<date>`, which holds the same commits.

## Keeping it cheap

After a `/project-review`, the packet takes about four steps. Batch the
reads into one shell call, and read a file's diff only where an item needs
it. Without a project review, don't run one inside the packet: say so, as
step 1 does, and let the user choose.

## Steps

1. **The findings.** Look back in this work session for a `/project-review`
   report on the range (its `ReportFindings` call). Nothing records which
   ranges Claude reviewed, so this conversation is the only place to find
   out.
   - If one ran on the range, its findings are item 7. If it covered only
     part (the uncommitted changes before they were committed, say), item 7
     names that part.
   - If none ran, the packet's first line says so: "No `/project-review`
     ran on this range in this work session. The findings come from the
     commits and the mistakes log. Run `/project-review` first for a full
     list." Item 7 then lists the fixes the commits' messages describe and
     the mistakes log's entries about the range's files and dates. Suggest
     `/project-review` to the user in the reply too.
2. **Read, in one batch:** `git log --oneline` and `git diff --stat` over the
   range; the diff of `tests/`; the added lines that log or print; the
   project imports of each touched source file; the tier table in
   `REVIEW.md` ("My reviews"); the mistakes log's pattern table ("At a
   glance") and index; and the facts register.
3. **Write the packet** to `drafts/review-packet-<date>.md` (Pacific date),
   for the user to read beside the pull request. Open it with the range and
   the pull request, or the branch it will come from if it isn't open yet,
   since `REVIEW.md` writes the packet first. Then:
   1. **Reading order.** Each touched file with its review tier and how the
      user reads it. Within a tier, a file comes after the project files it
      imports: modules with no project imports first, programs last. Name any
      path in no tier, with a question about its tier.
   2. **What changed.** For each file, two lines and the ADR.
   3. **Where it could be wrong.** Every check the mistakes log says is
      commonly missed or untested for this change, with no limit: each place
      in the change where a pattern with many entries could repeat, or where
      a mistake whose guard is "none yet" could, with the place, what to
      check and the mistake IDs. Read the log's pattern table and index, not
      every entry. Then anything else that could be wrong, and why.
   4. **Facts it relies on.** Each claim about cflib, the firmware, Python or
      Windows: in the facts register, checked in this review and added, or
      not checked.
   5. **New log messages**, each beside the condition that prints it.
   6. **New and changed tests**, by name and grouped by file, from the diff
      of `tests/`. The user reads them as a spec.
   7. **The findings** from step 1, and what happened to each.
   8. **Explain-back questions:** one for each significant change. Claude
      judges which changes are significant and says why each counted. Use
      only glossary terms, and put no answers in the packet.
4. **Hand it over.** Give the user the packet's path. The pull request's
   description names it. Committing, pushing and opening the pull request
   follow `REVIEW.md` ("My reviews"), each on the user's yes.

## Rules this keeps

- No commit, push or pull request without the user's yes. The packet lives
  in `drafts/`, which git ignores.
- It fixes nothing. Findings are the user's call, as in `/project-review`.
