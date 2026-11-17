---
name: review-packet
description: "Writes the review packet for one of the user's code reviews in the crazyflie-behavior repo, to drafts/review-packet-<date>.md, and posts the findings as comments on the review's pull request: the reading order of the source files by review tier, what changed in each and its ADR, new log messages, new and changed test names, the findings with their lines, and explain-back questions. Short and plain, for the user to read beside the pull request. Use it before one of the user's code reviews, right after /project-review in the same work session so the packet carries its findings. It also works on a range no project review covered, and says so. Argument: a commit range (default: from the last reviewed commit in REVIEW.md's review log to main)."
---

# Review packet

The user reads the code at review points, as a pull request in PyCharm. The
packet tells them, before the first file is opened, which files to read in
what order, what changed and why, and what the project review found. Its
explain-back questions show whether they can defend the change.

**It's for the user to read, not Claude.** Keep it short and plain:

- Plain sentences. No mistake IDs (M-172), REVIEW.md question numbers
  (Q-26), work-session names, or bare decision letters ("your C2"): say
  what was chosen.
- Ask the user to read only `.py` files outside `tests/`. Tests are read by
  their names (section 4); docs aren't read at review.
- Findings sit at their lines, as comments on the pull request, so PyCharm
  shows each one where the user is reading.

It's apart from `/project-review` because the two run at different times: a
project review before every commit to the safety layer, the Crazyflie
adapter or the tick loop, and a packet only before one of the user's code
reviews, over everything since the last one.

## Arguments

`/review-packet [range]`: a commit range. Default: from the "Reviewed up to"
commit in the last filled row of `REVIEW.md`'s review log to `main`. Once
the `reviewed` branch exists it marks the same commit. If the two disagree,
stop and ask: one of them is wrong, and the range would be too.

Before a review, `REVIEW.md` ("My reviews") runs it on
`reviewed..review/<date>`, which holds the same commits.

## Keeping it cheap

After a `/project-review`, the packet takes about four steps. Batch the
reads into one shell call. Without a project review, don't run one inside
the packet: say so, as step 1 does, and let the user choose.

## Steps

1. **The findings.** Look back in this work session for a `/project-review`
   report on the range (its `ReportFindings` call). Nothing records which
   ranges Claude reviewed, so this conversation is the only place to find
   out.
   - If one ran on the range, its findings are section 5. If it covered only
     part, section 5 says which part.
   - If none ran, the packet's first line says so: "No project review ran on
     this range in this work session; run `/project-review` first for a full
     list." Section 5 then lists the fixes the commits' messages describe.
     Suggest `/project-review` to the user in the reply too.
2. **Read, in one batch:** `git log --oneline` and `git diff --stat` over the
   range; the test names added or changed in `tests/`; the added lines that
   log or print; the project imports of each touched `.py` file; the tier
   table in `REVIEW.md` ("My reviews"); and, for each finding, the line it
   points at in the range's last commit, with line numbers.
3. **Write the packet** to `drafts/review-packet-<date>.md` (Pacific date).
   Open it with three lines: the range, the pull request (or the branch it
   will come from, since `REVIEW.md` writes the packet first), and which
   project review the findings come from. Then:
   1. **Reading order.** A table of each touched `.py` file outside `tests/`,
      with its review tier and how to read it (every line, or the diff).
      Within a tier, a file comes after the project files it imports. A
      `.py` file in no tier gets a one-line question about its tier.
   2. **What changed.** Two plain lines per file in the reading order, with
      its ADR. Then one line naming the ADRs the range adds or amends.
   3. **New log messages**, each beside the condition that prints it.
   4. **New and changed tests**, by name, grouped by file. The user reads
      them as a spec.
   5. **Findings.** A table: the finding in a few plain words, where it is
      (`file:line`), and what happened to it. Each one is also a comment on
      the pull request (step 4).
   6. **Explain-back questions:** one for each significant change, with a few
      words on why it counted. Use only glossary terms, and put no answers in
      the packet or the comments.
4. **The comments.** Draft one per finding, at its line in the pull
   request's last commit. Each starts with **"Claude:"**, since they post
   under the user's GitHub account and the user's own comments are the
   review's record. One or two sentences: the finding, then its outcome. A
   line comment only attaches to a line inside the pull request's diff; a
   finding with no such line goes in the review's summary instead. Post them
   without asking (the user's standing yes), as one review:

   ```bash
   gh api repos/<owner>/<repo>/pulls/<number>/reviews --input <review.json>
   ```

   with `commit_id` set to the pull request's last commit, `event` set to
   `COMMENT`, the summary in `body`, and each comment as `path`, `line`,
   `side: "RIGHT"`, `body`. Write the JSON to the scratchpad. Then check
   each comment's `path` and `line` in the pull request's comments. If the
   pull request isn't open yet, post them right after it's opened.
5. **Hand it over.** Give the user the packet's path and the pull request's
   link. The pull request's description names the packet. Committing,
   pushing and opening the pull request follow `REVIEW.md` ("My reviews"),
   each on the user's yes.

## Rules this keeps

- No commit, push or pull request without the user's yes. Comments on the
  review's pull request need none. The packet lives in `drafts/`, which git
  ignores.
- It fixes nothing. Findings are the user's call, as in `/project-review`.
