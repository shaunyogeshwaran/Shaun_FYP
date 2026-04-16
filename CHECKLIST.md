# FYP Submission Checklist

**Module:** 6COSC023W - Computer Science Final Project
**Weighting:** 70%
**Deadline:** 30/03/2026 at 13:00 (no extensions)
**Viva:** Date TBC by supervisor (1 hour, supervisor + moderator)

All four elements (FPR + FPC + FVD + FPV) must be attempted for the FYP to be marked. They produce one combined mark.

---

## 1. Final Project Report (FPR) - 100% of report mark

### Preliminary Sections (10% of report)

- [ ] Cover page with actual project title (not placeholder)
- [ ] Student name and supervisor name on title page
- [ ] Declaration section completed (word count, name, date of submission)
- [ ] Abstract summarising the entire project
- [ ] Acknowledgements
- [ ] Table of contents (correctly numbered, matches report structure)
- [ ] List of figures (correctly numbered)
- [ ] List of tables (correctly numbered)
- [ ] All orange template sections deleted from final version
- [ ] Structured writing style with clear connections across chapters
- [ ] References — Harvard style, all cited sources listed
- [ ] Bibliography — additional readings
- [ ] Appendices (requirement data, evaluation data, key code, etc.)

### Report Chapters (40% of report)

- [ ] **Ch 1. Introduction**
  - [ ] 1.1 Problem statement
  - [ ] 1.2 Aims and objectives (clear, achievable)
- [ ] **Ch 2. Background**
  - [ ] 2.1 Literature survey
  - [ ] 2.2 Review of projects/applications
  - [ ] 2.3 Review of tools, frameworks and techniques
  - [ ] Balanced evaluation of advantages/disadvantages, gaps identified
- [ ] **Ch 3. Legal, Social and Ethical Issues**
  - [ ] Legal, ethical, social, professional and security issues covered
  - [ ] Issues related to software/data infrastructure and data collected/analysed
- [ ] **Ch 4. Methodology**
  - [ ] Critical review of methodology used
  - [ ] Technical design solutions addressing requirements
  - [ ] Contribution to knowledge/practice demonstrated
- [ ] **Ch 8. Conclusions and Reflections**
  - [ ] Conclusions on the resulting application
  - [ ] New knowledge and skills acquired
  - [ ] Further work to improve the application

### Technical Chapters (50% of report)

- [ ] **Ch 5. Design**
  - [ ] Appropriate design methods used
  - [ ] Diagrams/prototypes depicting the design
  - [ ] Design follows requirements
  - [ ] Originality demonstrated
  - [ ] Design issues related to models/software/data infrastructure
- [ ] **Ch 6. Tools and Implementation**
  - [ ] 6.1 All tools listed with justification for why they were chosen
  - [ ] 6.2 In-depth explanation of main code for key functions
  - [ ] Clear indication of novel code vs adopted/adapted code with sources
  - [ ] Critical evaluation if core functionality not implemented
  - [ ] Originality clearly presented
  - [ ] Demonstration of significant new technical skills gained
  - [ ] Code executes without issues/errors
- [ ] **Ch 7. Testing**
  - [ ] 7.1 Functional testing (black box and/or white box)
  - [ ] 7.2 User testing
  - [ ] All results critically discussed
  - [ ] Suggestions for further developments based on testing outcomes

### Report Submission

- [ ] File format: DOCX or PDF only (no other types)
- [ ] File size under 10MB
- [ ] NOT zipped
- [ ] Demo video link included in Appendix I
- [ ] Submit on Blackboard by deadline

---

## 2. Final Project Code (FPC)

- [ ] Code is complete and functional
- [ ] `make start` runs without errors
- [ ] `make install` instructions work from clean checkout
- [ ] README.md explains all steps to run the project
- [ ] Code zipped for submission
- [ ] If ZIP < 50MB: upload on Blackboard with report
- [ ] If ZIP > 50MB: upload to University OneDrive, share link in Appendix I
  - [ ] OneDrive sharing: "People in University of Westminster"
  - [ ] "Block download" OFF
  - [ ] Link pasted in Appendix I
- [ ] GitHub repo link included in report/appendix
- [ ] Access maintained until final grade confirmation (end of summer)

---

## 3. Final Project Video Demo (FVD)

- [ ] Screen capture showing user interface
- [ ] All functionalities demonstrated
- [ ] How-to-use demonstration
- [ ] Voiceover explaining/describing the product
- [ ] Clear video and audio quality
- [ ] Uploaded to OneDrive/YouTube/other platform
- [ ] Link included in Appendix I of report
- [ ] Link accessible until end of summer (grade confirmation)

---

## 4. Final Project Viva (FPV)

- [ ] Prepared to demonstrate practical output live (1 hour)
- [ ] Can explain the development process end-to-end
- [ ] Understand wider context of the work
- [ ] Ready to discuss relevant issues (ethical, legal, technical)
- [ ] Can propose further work
- [ ] `make start` tested and working for live demo

---

## Progress Summary (as of 2026-04-16)

| Component | Status | Notes |
|-----------|--------|-------|
| **FPR (Thesis)** | DONE | Completed thesis document |
| **FPC (Code)** | DONE | Codebase finalized, reviewed, all PRs merged |
| **FVD (Video)** | TODO | Screen capture with voiceover needed |
| **FPV (Viva)** | TODO | Prepare for 1-hour oral exam, live demo |
| **Submission** | TODO | Upload FPR + FPC + video link to Blackboard |

### Code Status

- Codebase reviewed and finalized (PR #30 merged)
- Docs link added to frontend (PR #32 merged)
- README with full setup instructions present
- `make start` launches backend (:8000) + frontend (:5173) + docs (:4000)
- All experiment results in `results/` directory
- Docusaurus documentation site functional

### Remaining Tasks

1. **Record demo video** — screen capture of frontend (Verify, Explore, About pages), show v1 vs v2 mode, offline mode, threshold controls. Add voiceover.
2. **Upload video** — OneDrive (UoW sharing) or YouTube, get shareable link
3. **Final report check** — ensure video link is in Appendix I, declaration completed, orange sections removed, file < 10MB
4. **Zip code** — zip entire project, check size for BB upload vs OneDrive
5. **Submit on Blackboard** — FPR file + FPC zip (or OneDrive link) before 30/03/2026 13:00
6. **Viva prep** — practice live demo, prepare to explain pipeline, methodology, results, further work
