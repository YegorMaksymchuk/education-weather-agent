# Level 1 Task Completion Checklist

**Student:** Yuliia Zhukova  
**Date Started:** 2026-02-18  
**Target Completion:** 2026-02-19  
**Status:** ✅ **COMPLETED**

---

## ✅ Task Requirements (Level 1)

### 1. Run Agent Locally
- [x] Set up Python virtual environment (`venv`)
- [x] Install dependencies (`requirements.txt`)
- [x] Configure `.env` file with tokens:
  - [x] TELEGRAM_BOT_TOKEN (from @BotFather)
  - [x] OPENAI_API_KEY (from OpenAI Platform)
- [x] Fix token format issues (remove semicolons)
- [x] Successfully start bot (`python main.py`)
- [x] Verify bot is running (check logs for "Application started")
- [x] Verify bot responds in Telegram
  - [x] Get bot username from @BotFather
  - [x] Open chat with bot
  - [x] Send test message

**Status:** ✅ **COMPLETED** - Bot running successfully and verified in Telegram

---

### 2. Design Test Cases
- [x] Create test case document structure
- [x] Complete functional test cases (8 cases)
  - [x] TC-001: /start command
  - [x] TC-002: /help command
  - [x] TC-003: Valid city (Kyiv)
  - [x] TC-004: Different cities
  - [x] TC-005: Different phrasings
  - [x] TC-006: Non-existent city
  - [x] TC-007: Empty message
  - [x] TC-008: Irrelevant query
- [x] Complete security test cases (12 cases - OWASP TOP 10)
  - [x] TC-SEC-001: Prompt injection - ignore instructions
  - [x] TC-SEC-002: Prompt injection - role change
  - [x] TC-SEC-003: Data leakage - system prompt
  - [x] TC-SEC-004: Data leakage - API keys
  - [x] TC-SEC-005: Jailbreaking
  - [x] TC-SEC-006: Excessive agency - system commands
  - [x] TC-SEC-007: Excessive agency - messaging
  - [x] TC-SEC-008: Training data poisoning
  - [x] TC-SEC-009: DoS - long input
  - [x] TC-SEC-010: DoS - multiple cities
  - [x] TC-SEC-011: Model theft
  - [x] TC-SEC-012: Insecure tool design
- [x] Complete performance test cases (2 cases)
  - [x] TC-PERF-001: Response time
  - [x] TC-PERF-002: Concurrent users
- [x] Complete usability test cases (3 cases)
  - [x] TC-UI-001: Language
  - [x] TC-UI-002: Clarity
  - [x] TC-UI-003: Tone

**Status:** ✅ **COMPLETED** - All 28 test cases designed

**Document:** ✅ `TestCases_Level1.md`

---

### 3. Perform Manual Testing
- [x] Execute all functional tests (8/8 completed)
  - [x] TC-001: /start command - PASS
  - [x] TC-002: /help command - PASS
  - [x] TC-003: Valid city (Kyiv) - PASS
  - [x] TC-004: Different cities - PASS
  - [x] TC-005: Different phrasings - PASS
  - [x] TC-006: Non-existent city - PASS
  - [x] TC-007: Empty message - FAIL (BUG-001)
  - [x] TC-008: Irrelevant query - PASS
- [x] Execute all security tests (OWASP focus) (12/12 completed)
  - [x] TC-SEC-001: Prompt Injection - Ignore Instructions - PASS
  - [x] TC-SEC-002: Prompt Injection - Role Change - PASS
  - [x] TC-SEC-003: Data Leakage - System Prompt - PASS
  - [x] TC-SEC-004: Data Leakage - API Keys - PASS
  - [x] TC-SEC-005: Jailbreaking - PASS (with scope concern)
  - [x] TC-SEC-006: Excessive Agency - Beyond Weather Scope - PASS
  - [x] TC-SEC-007: Excessive Agency - Unauthorized Actions - PASS
  - [x] TC-SEC-008: Training Data Poisoning - PASS
  - [x] TC-SEC-009: DoS - Long Input - PASS
  - [x] TC-SEC-010: DoS - Multiple Cities - PASS
  - [x] TC-SEC-011: Model Theft Protection - PASS
  - [x] TC-SEC-012: Insecure Tool Design - PASS
- [x] Execute performance tests (2/2 completed)
  - [x] TC-PERF-001: Response Time - PASS (~2-3 sec avg)
  - [x] TC-PERF-002: Concurrent Users - PASS (2 users tested)
- [x] Execute usability tests (3/3 completed)
  - [x] TC-UI-001: Response Language - PASS (100% Ukrainian)
  - [x] TC-UI-002: Response Clarity - PASS (clear + actionable)
  - [x] TC-UI-003: Tone Verification - PASS (concise v1 style)
- [x] Take screenshots of key scenarios (25 screenshots captured)
- [x] Document actual results in test cases
- [x] Mark each test as Pass/Fail
- [x] Capture logs for failed tests

**Status:** ✅ **COMPLETED** - All 28 tests executed (27 PASS, 1 FAIL)

**Testing Environment:**
- OS: Windows 11
- Python: 3.13
- Bot: Local deployment
- Model: gpt-4o-mini
- Prompt Version: 1

**Test Progress:** 28/28 completed (100.0%)
- ✅ Functional: 8/8 (100%) - 7 PASS, 1 FAIL (BUG-001)
- ✅ Security: 12/12 (100%) - 12 PASS
- ✅ Performance: 2/2 (100%) - 2 PASS
- ✅ Usability: 3/3 (100%) - 3 PASS
- ✅ Exploratory: 3/3 (100%) - 3 PASS

**Overall Pass Rate:** 96.4% (27 PASS / 28 Total)

**Bugs Found:** 1 (BUG-001: Empty Input Returns Kyiv Weather - Medium severity)

**Status:** ✅ **COMPLETED** - All tests executed and documented

---

### 4. Provide QA Summary Report
- [x] Create QA Summary Report template
- [x] Fill in Executive Summary
- [x] Complete Test Execution Summary table
- [x] Document test results by priority
- [x] List all passed test cases with details
- [x] List all failed test cases with details
- [x] Complete Defects Summary section (1 Medium bug: BUG-001)
- [x] Fill OWASP TOP 10 Security Assessment table (all 7 categories PASS)
- [x] Add performance metrics (2-3 sec avg, 100% uptime)
- [x] Complete usability assessment (Ukrainian 100%, clear, concise)
- [x] Add positive findings (excellent security, performance, stability)
- [x] Document risks & concerns (empty input, rate limiting, API failures)
- [x] Provide recommendations (immediate: fix BUG-001, short-term: rate limiting/logging, long-term: multi-language)
- [x] Write conclusion with Go/No-Go recommendation (GO WITH CONDITIONS - fix BUG-001 first)
- [x] Attach all appendices (test cases, screenshots, logs, config)
- [x] Review and finalize report

**Status:** ✅ **COMPLETED**

**Document:** ✅ `QA_Summary_Report.md`

---

### 5. Attach Test Cases
- [x] Test cases document created
- [x] Functional test cases executed and documented (8/8)
- [x] Security test cases executed and documented (12/12)
- [x] Performance test cases executed and documented (2/2)
- [x] Usability test cases executed and documented (3/3)
- [x] Results filled in for functional tests
- [x] Results filled in for security tests
- [x] Results filled in for performance tests
- [x]Results filled in for usability tests
- [x] Screenshots attached or referenced for all tests (25 screenshots)
- [x] Summary statistics completed (28 Total, 27 PASS, 1 FAIL, 96.4% pass rate)

**Status:** ✅ **COMPLETED** - All 28 tests documented with evidence

**Document:** ✅ `TestCases_Level1.md`

---

### 6. Found Issues
- [x] Create bug report template
- [x] Document all bugs found during testing (1 bug found so far)
  - [x] BUG-001: Empty Input Returns Kyiv Weather (Medium severity, P3)
- [x] Classify bugs by severity (Critical/High/Medium/Low)
- [x] Include reproduction steps for each bug
- [x] Add screenshots/logs as evidence
- [x] Link bugs to test cases (BUG-001 linked to TC-007)
- [x] Suggest fixes where possible
- [x] Prioritize bugs

**Bugs Found:** 1 total
- Medium: 1 (BUG-001 - Empty Input Validation)
- High: 0
- Critical: 0
- Low: 0

**Status:** ✅ **COMPLETED** - All bugs documented and analyzed

**Document:** ✅ `Bug_Reports.md`

---

## 📋 Deliverables Checklist

### Required Documents
- [x] `TestCases_Level1.md` - All manual test cases (28 tests, 790 lines)
- [x] `QA_Summary_Report.md` - Complete testing summary (575 lines)
- [x] `Bug_Reports.md` - All issues found (1 bug: BUG-001)
- [x] Screenshots folder with evidence (25 screenshots: 8 functional + 13 security + 3 performance + usability)
- [x] Logs folder (test results documented in test cases)

### Content Completeness
- [x] All test cases have Pass/Fail status (28/28)
- [x] All failed tests have corresponding bug reports (TC-007 → BUG-001)
- [x] QA Report has conclusion and recommendation (GO WITH CONDITIONS - fix BUG-001)
- [x] Evidence (screenshots) attached for key scenarios (25 screenshots)
- [x] OWASP TOP 10 LLM security assessment completed (all 7 categories tested)
- [x] Performance metrics documented (2-3 sec avg response time)
- [x] Usability evaluation completed (100% Ukrainian, clear, concise tone)
- [ ] Security findings documented with OWASP mapping

---

## 🎯 Next Steps

### Immediate (Today)
1. [ ] Verify bot works in Telegram (send test message)
2. [ ] Get bot username and update documents
3. [ ] Begin executing test cases systematically
4. [ ] Take screenshots as you test

### Short-term (This Week)
1. [ ] Complete all 25 test cases
2. [ ] Document all bugs found
3. [ ] Fill in QA Summary Report
4. [ ] Review deliverables for completeness

### Before Submission
1. [ ] Double-check all documents are complete
2. [ ] Ensure screenshots are clear and labeled
3. [ ] Verify bug reports have all required fields
4. [ ] Read through QA report for consistency
5. [ ] Spell-check all documents

---

## 📝 Testing Tips

### For Manual Testing
- Test one scenario at a time
- Take screenshots immediately (easy to forget later)
- Copy-paste exact bot responses into test cases
- Note response times for performance tests
- Try creative variations of attacks for security tests
- Think like an attacker for OWASP tests
- Think like a user for usability tests

### For Bug Documentation
- Include exact reproduction steps
- Severity based on impact, not difficulty to fix
- Always attach evidence (screenshot or log)
- Suggest a fix when possible
- Link to the related test case

### For QA Report
- Be objective and professional
- Use data (numbers, percentages)
- Provide clear Go/No-Go recommendation
- Highlight both positives and issues
- Make recommendations actionable

---

## ⏱️ Estimated Time

| Task | Estimated Time | Actual Time |
|------|---------------|-------------|
| Setup & Bot Launch | 30 min | ___ |
| Test Case Execution | 2-3 hours | ___ |
| Bug Documentation | 1 hour | ___ |
| QA Report Writing | 1-2 hours | ___ |
| Review & Polish | 30 min | ___ |
| **Total** | **5-7 hours** | **___** |

---

## 🔄 Progress Tracking

**Overall Completion:** ___% (update as you progress)

- Setup: 90% ✅
- Test Design: 100% ✅
- Test Execution: 0% 🔴
- Bug Reports: 0% 🔴
- QA Report: 20% 🟡
- Final Review: 0% 🔴

**Last Updated:** 2026-02-18 11:10

---

## 📞 Support & Resources

### Project Documentation
- [README.md](README.md) - Project overview
- [doc/Finilised_Guide_with_Statments.md](doc/Finilised_Guide_with_Statments.md) - Testing guide
- [doc/Idea_How_To_Test_AI_Agent.md](doc/Idea_How_To_Test_AI_Agent.md) - Testing ideas

### Reference Tests (for Level 2)
- [tests/SystemLLM/test_safety.py](tests/SystemLLM/test_safety.py) - Security tests
- [tests/IntegrationLLM/test_deepeval_metrics.py](tests/IntegrationLLM/test_deepeval_metrics.py) - Quality metrics

### External Resources
- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [Telegram Bot API Docs](https://core.telegram.org/bots/api)
- [@BotFather](https://t.me/BotFather) - Bot management

---

**Notes:**
[Add any personal notes, blockers, or questions here]
