# QA Documentation

This folder contains Quality Assurance documentation for the Weather Agent project.

## Level 1: Manual Testing

### Documents

1. **[Level1_Checklist.md](Level1_Checklist.md)** - Task completion checklist
   - Track progress of all Level 1 requirements
   - Estimated time and status tracking
   - Links to all deliverables

2. **[TestCases_Level1.md](TestCases_Level1.md)** - Manual test cases
   - 28 test cases covering:
     - Functional testing (8 cases)
     - Security testing - OWASP TOP 10 for LLM (12 cases)
     - Performance testing (2 cases)
     - Usability testing (3 cases)
   - Each test case includes:
     - Priority, steps, expected results
     - Space for actual results and screenshots
     - Pass/Fail status tracking

3. **[QA_Summary_Report.md](QA_Summary_Report.md)** - Executive testing summary
   - Test execution statistics
   - Defects summary with severity classification
   - OWASP TOP 10 security assessment
   - Performance metrics
   - Recommendations and conclusions
   - Go/No-Go release decision

4. **[Bug_Reports.md](Bug_Reports.md)** - Issue tracking
   - Bug report template
   - Severity guidelines (Critical/High/Medium/Low)
   - Example bug reports
   - Space to document all found issues

### Screenshots

Store test evidence in the [screenshots/](screenshots/) folder:
- Name format: `TC-XXX_description.png`
- Example: `TC-SEC-001_prompt_injection_test.png`

## Level 2: Automated Testing

(Documentation will be added after Level 2 completion)

## Usage

### For Testing
1. Start with [Level1_Checklist.md](Level1_Checklist.md)
2. Execute tests from [TestCases_Level1.md](TestCases_Level1.md)
3. Document bugs in [Bug_Reports.md](Bug_Reports.md)
4. Summarize results in [QA_Summary_Report.md](QA_Summary_Report.md)

### For Submission
Ensure all documents are complete:
- [ ] All test cases executed (Pass/Fail marked)
- [ ] Screenshots attached
- [ ] Bugs documented with evidence
- [ ] QA Report filled with conclusion

## Testing Focus

### Security (OWASP TOP 10 for LLM)
- LLM01: Prompt Injection
- LLM03: Training Data Poisoning
- LLM04: Denial of Service
- LLM06: Sensitive Information Disclosure
- LLM07: Insecure Plugin Design
- LLM08: Excessive Agency
- LLM10: Model Theft

### Key Functional Areas
- Telegram bot commands (/start, /help)
- Weather query processing
- City name handling (valid, invalid, special characters)
- Error handling and user feedback
- Response language and tone

## Resources

- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- Project docs: [../Finilised_Guide_with_Statments.md](../Finilised_Guide_with_Statments.md)
- Existing tests: [../../tests/](../../tests/)

---

**Last Updated:** 2026-02-18  
**Tester:** Yuliia Zhukova
