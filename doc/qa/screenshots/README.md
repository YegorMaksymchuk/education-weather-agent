# Screenshots Organization

This directory contains test execution screenshots organized by test category.

## 📁 Folder Structure

```
screenshots/
├── functional/          # Functional test cases (TC-001 to TC-008)
├── security/            # Security test cases (TC-SEC-001 to TC-SEC-012)
├── performance/         # Performance test cases (TC-PERF-001, TC-PERF-002)
└── usability/           # Usability test cases (TC-UI-001 to TC-UI-003)
```

## 📝 Naming Convention

Screenshots follow this naming pattern:
```
TC-[CATEGORY]-[NUMBER]_[description].png
```

**Examples:**
- `TC-001_start_command.png` - Functional test
- `TC-SEC-005_jailbreaking_1.png` - Security test (with sequence number)
- `TC-PERF-001_response_time.png` - Performance test
- `TC-UI-002_clarity.png` - Usability test

## 🔗 Linking from Test Cases

In `TestCases_Level1.md`, screenshots are referenced using relative paths:

```markdown
**Screenshot:** [TC-001_start_command.png](screenshots/functional/TC-001_start_command.png)
```

This creates a clickable link that opens the screenshot in VS Code.

## 📊 Current Statistics

- **Functional:** 8 screenshots
- **Security:** 13 screenshots (including multi-part tests)
- **Performance:** 1 screenshot (1 pending)
- **Usability:** 0 screenshots (3 pending)

**Total:** 22 screenshots

---

**Last Updated:** 2026-02-18  
**Tester:** Yuliia Zhukova
