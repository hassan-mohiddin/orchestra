# Mermaid Syntax Troubleshooting Guide

**Version:** 1.0
**Last Updated:** 2025-01-13
**Purpose:** Common syntax errors and how to fix them

This guide documents the top 20+ most common Mermaid syntax errors discovered through research of GitHub issues, Stack Overflow questions, and community forums.

---

## Table of Contents

1. [Quick Validation](#quick-validation)
2. [Cross-Cutting Issues (All Diagrams)](#cross-cutting-issues-all-diagrams)
3. [Flowchart & Graph Diagrams](#flowchart--graph-diagrams)
4. [Sequence Diagrams](#sequence-diagrams)
5. [Class Diagrams](#class-diagrams)
6. [State Diagrams](#state-diagrams)
7. [ER Diagrams](#er-diagrams)
8. [Gantt Charts](#gantt-charts)
9. [Pie Charts](#pie-charts)
10. [General Resources](#general-resources)

---

## Quick Validation

**Before debugging syntax manually, use the validation scripts:**

```bash
# Validate all diagrams in a markdown file
python scripts/extract_mermaid.py your-file.md --validate

# Convert to image to verify rendering
python scripts/mermaid_to_image.py diagram.mmd output.png
```

**Common Quick Fixes:**
- ✅ Wrap reserved words in double quotes
- ✅ Check for missing closing `end` keywords in blocks
- ✅ Ensure colons exist before message text in sequence diagrams
- ✅ Verify arrow syntax (must be `-->`, not `->`)
- ✅ Escape special characters with quotes or HTML entities

---

## Cross-Cutting Issues (All Diagrams)

### ❌ Error 1: Reserved Words as Identifiers

**Severity:** 🔴 Critical - Causes immediate parse failure

**Problem:** Using reserved keywords without quotes breaks the parser.

**Reserved Words Include:**
- `default`, `style`, `class`, `end`, `subgraph`, `click`
- `interpolate`, `classDef`, `linkStyle`, `call`, `graph`
- `_self`, `_blank`, `_parent`, `_top`

**Incorrect:**

```mermaid
flowchart TD
    start --> end
    call --> style
```

**Correct:**

```mermaid
flowchart TD
    start --> "end"
    "call" --> "style"
```

**Error Message:**
- `Parse error on line X: ... got 'DEFAULT'`
- `Syntax error in text`

**Diagram Types Affected:** All diagrams (especially flowcharts, state diagrams, Gantt charts)

---

### ❌ Error 2: Unescaped Special Characters

**Severity:** 🟠 High - Breaks rendering or causes silent failures

**Problem:** Special characters in labels must be escaped or wrapped in quotes.

**Special Characters:**
- Double quotes: `"`
- Parentheses: `(` `)`
- Brackets: `[` `]` `{` `}`
- Backslash: `\`
- Colon: `:`, Semicolon: `;`, Comma: `,`
- Hash: `#`, Percent: `%`, At: `@`

**Incorrect:**

```mermaid
flowchart TD
    A[Say "hello"]
    B[Domain\User1]
    C[Object(foo,bar)]
```

**Correct:**

```mermaid
flowchart TD
    A["Say #34;hello#34;"]
    B["Domain\User1"]
    C["Object(foo,bar)"]
```

**Alternative:**

```mermaid
flowchart TD
    A["Say &quot;hello&quot;"]
    B["Domain\\User1"]
    C["Object#40;foo,bar#41;"]
```

**Diagram Types Affected:** All diagrams

**Best Practice:** When in doubt, wrap the entire label in double quotes.

---

### ❌ Error 3: Invalid classDef Syntax

**Severity:** 🟡 Medium - Styling won't apply

**Problem:** Using curly braces or semicolons in classDef declarations.

**Incorrect:**

```mermaid
flowchart TD
    classDef myClass {
        fill: #ff0000;
        stroke: #333;
    }
```

**Also Incorrect:**

```mermaid
stateDiagram-v2
    classDef badEvent fill:#f00;color:white
```

**Correct:**

```mermaid
flowchart TD
    classDef myClass fill:#ff0000,stroke:#333,color:#fff
```

**Explanation:**
- No curly braces allowed
- Use comma or space to separate properties
- No semicolons (only CSS-like property:value pairs)

**Diagram Types Affected:** Flowcharts, state diagrams

---

### ❌ Error 4: Empty Comments

**Severity:** 🟢 Low - But causes syntax errors in some parsers

**Problem:** Comment marker `%%` without any following text.

**Incorrect:**

```mermaid
gantt
    %%
    section Tasks
    Task 1 : 2024-01-01, 3d
```

**Correct:**

```mermaid
gantt
    %% This is a comment
    section Tasks
    Task 1 : 2024-01-01, 3d
```

**Diagram Types Affected:** All diagrams (especially Gantt charts)

---

## Flowchart & Graph Diagrams

### ❌ Error 5: Reserved Word "end" in Node Names

**Severity:** 🔴 Critical

**Problem:** The word "end" is reserved and breaks flowcharts.

**Incorrect:**

```mermaid
flowchart TD
    start --> end
```

**Correct Solutions:**

```mermaid
flowchart TD
    start --> End
    %% OR
    start --> "end"
    %% OR
    start --> endNode[end]
```

**Error Message:** Parser treats "end" as keyword, not node ID

---

### ❌ Error 6: Node IDs Starting with "o" or "x"

**Severity:** 🟠 High - Creates unintended edge types

**Problem:** Starting a node ID with `o` or `x` conflicts with edge markers.

**Incorrect:**

```mermaid
flowchart LR
    dev---ops
    %% Creates circle edge instead of connecting to "ops"
```

**Correct:**

```mermaid
flowchart LR
    dev--- ops
    %% Note: space before "ops"
    %% OR
    dev---Ops
```

**Explanation:** Parser interprets `---o` as circle edge marker and `---x` as cross edge marker.

---

### ❌ Error 7: Incorrect Arrow/Link Syntax

**Severity:** 🔴 Critical - Prevents connections

**Problem:** Missing dashes or using wrong arrow syntax.

**Incorrect:**

```mermaid
flowchart TD
    A - B
    %% Single dash
    C -> D
    %% Two characters instead of three
    E .-> F
    %% Deprecated dotted syntax
```

**Correct:**

```mermaid
flowchart TD
    A --> B
    %% Standard arrow (3 characters)
    C -.-> D
    %% Dotted arrow (must be -.->)
    E ==> F
    %% Thick arrow
```

**Valid Arrow Types:**
- `-->` Standard arrow
- `-.->` Dotted arrow
- `==>` Thick arrow
- `---` No arrow (line only)
- `-.-` Dotted line

---

### ❌ Error 8: Incorrect Node Bracket Syntax

**Severity:** 🔴 Critical

**Problem:** Missing or mismatched brackets around node labels.

**Incorrect:**

```mermaid
flowchart TD
    A[Start --> B[Process]]
```

**Correct:**

```mermaid
flowchart TD
    A[Start] --> B[Process]
```

**Node Shape Reference:**
- `[]` Rectangle
- `()` Rounded
- `[[]]` Subroutine
- `[()]` Stadium
- `{}` Diamond
- `{{}}` Hexagon
- `[/\]` Trapezoid
- `[\]` Reverse trapezoid

---

### ❌ Error 9: Diagram Direction on Same Line as Nodes

**Severity:** 🔴 Critical

**Problem:** Diagram type and direction must be on a separate line.

**Incorrect:**

```mermaid
flowchart TD A --> B
```

**Correct:**

```mermaid
flowchart TD
    A --> B
```

---

### ❌ Error 10: Nested Subgraph Linking Error

**Severity:** 🟠 High - Causes unexpected behavior

**Problem:** Linking to both a parent subgraph and a nested subgraph within it.

**Incorrect:**

```mermaid
flowchart TD
    sender1 --> system
    sender2 --> subsystem

    subgraph system
        subgraph subsystem
            service1
        end
    end
```

**Correct:**

```mermaid
flowchart TD
    sender1 --> service1
    sender2 --> service1

    subgraph system
        subgraph subsystem
            service1
        end
    end
```

**Explanation:** Link directly to nodes inside nested subgraphs, not to the subgraph itself.

---

## Sequence Diagrams

### ❌ Error 11: Missing Colon Before Message Text

**Severity:** 🔴 Critical

**Problem:** Colon is required to separate arrow from message.

**Incorrect:**

```mermaid
sequenceDiagram
    Alice->>Bob Message
```

**Correct:**

```mermaid
sequenceDiagram
    Alice->>Bob: Message
```

---

### ❌ Error 12: Missing Space in Participant Declaration

**Severity:** 🔴 Critical

**Problem:** No space between "participant" keyword and participant name.

**Incorrect:**

```mermaid
sequenceDiagram
    participantAlice
```

**Correct:**

```mermaid
sequenceDiagram
    participant Alice
```

---

### ❌ Error 13: Missing "end" in alt/opt/loop Blocks

**Severity:** 🔴 Critical - Causes parse errors

**Problem:** Forgetting to close blocks with "end" keyword.

**Incorrect:**

```mermaid
sequenceDiagram
    Alice->>Bob: Request
    alt Success
        Bob->>Alice: OK
    else Failure
        Bob->>Alice: Error
```

**Correct:**

```mermaid
sequenceDiagram
    Alice->>Bob: Request
    alt Success
        Bob->>Alice: OK
    else Failure
        Bob->>Alice: Error
    end
```

**Affected Blocks:** `alt`, `opt`, `loop`, `par`, `rect`, `break`, `critical`

---

### ❌ Error 14: Misplaced Activation Boxes

**Severity:** 🟡 Medium - Visual issues

**Problem:** Placing activate/deactivate in wrong positions.

**Incorrect:**

```mermaid
sequenceDiagram
    Alice->>Bob: Request
    Bob-->>Alice: Response
    activate Bob
```

**Correct:**

```mermaid
sequenceDiagram
    Alice->>Bob: Request
    activate Bob
    Bob-->>Alice: Response
    deactivate Bob
```

**Alternative (shorthand):**

```mermaid
sequenceDiagram
    Alice->>+Bob: Request
    Bob-->>-Alice: Response
```

---

### ❌ Error 15: Participant Names Starting with 'x'

**Severity:** 🟠 High - Conflicts with deactivation syntax

**Problem:** Names starting with 'x' are confused with `-x` deactivation shorthand.

**Incorrect:**

```mermaid
sequenceDiagram
    xAlice->>+John: Hello
    John-->>-xAlice: Hi
```

**Correct:**

```mermaid
sequenceDiagram
    Alice->>+John: Hello
    John-->>Alice: Hi
    deactivate John
```

**Solution:** Avoid participant names starting with 'x' or use explicit `deactivate` instead of `-` shorthand.

---

## Class Diagrams

### ❌ Error 16: Missing Quotes in Cardinality Notation

**Severity:** 🔴 Critical

**Problem:** Cardinality values must be in quotes.

**Incorrect:**

```mermaid
classDiagram
    Customer 1 --> * Order
```

**Correct:**

```mermaid
classDiagram
    Customer "1" --> "*" Order
```

---

### ❌ Error 17: Missing Parentheses in Method Declarations

**Severity:** 🟡 Medium - Methods appear as properties

**Problem:** Methods require parentheses even with no parameters.

**Incorrect:**

```mermaid
classDiagram
    class Animal {
        +int age
        +move
    }
```

**Correct:**

```mermaid
classDiagram
    class Animal {
        +int age
        +move()
    }
```

---

### ❌ Error 18: Incorrect Static/Abstract Modifier Placement

**Severity:** 🟡 Medium

**Problem:** Static ($) and abstract (*) must come AFTER the signature.

**Incorrect:**

```mermaid
classDiagram
    class MyClass {
        +$staticMethod()
        +*abstractMethod()
    }
```

**Correct:**

```mermaid
classDiagram
    class MyClass {
        +staticMethod()$
        +abstractMethod()*
    }
```

---

## State Diagrams

### ❌ Error 19: State Names Starting with 'x'

**Severity:** 🟠 High - Conflicts with deactivation syntax

**Problem:** State names starting with 'x' are confused with arrow modifiers.

**Incorrect:**

```mermaid
stateDiagram-v2
    Still --> xAlice
    xAlice --> Moving
```

**Correct:**

```mermaid
stateDiagram-v2
    Still --> Alice
    Alice --> Moving
```

---

### ❌ Error 20: Incorrect State Description Syntax

**Severity:** 🔴 Critical

**Problem:** Using colon instead of "as" keyword with state descriptions.

**Incorrect:**

```mermaid
stateDiagram-v2
    state "This is a description": s2
```

**Correct:**

```mermaid
stateDiagram-v2
    state "This is a description" as s2
```

---

### ❌ Error 21: ClassDef on Special States

**Severity:** 🟡 Medium

**Problem:** Classes cannot be applied to `[*]` (start/end states).

**Incorrect:**

```mermaid
stateDiagram-v2
    classDef myClass fill:#f00
    class [*] myClass
```

**Correct:**

```mermaid
stateDiagram-v2
    classDef myClass fill:#f00
    class NormalState myClass
    [*] --> NormalState
```

---

## ER Diagrams

### ❌ Error 22: Wrong Attribute Order

**Severity:** 🔴 Critical

**Problem:** Attribute type must come BEFORE the name.

**Incorrect:**

```mermaid
erDiagram
    Order {
        id int
        amount float
    }
```

**Correct:**

```mermaid
erDiagram
    Order {
        int id
        float amount
    }
```

**Error Message:** `Expected ATTRIBUTE_WORD but found BLOCK_STOP`

---

### ❌ Error 23: Invalid Relationship Syntax

**Severity:** 🔴 Critical

**Problem:** Using incomplete relationship notation.

**Incorrect:**

```mermaid
erDiagram
    Order |-- Customer
```

**Correct:**

```mermaid
erDiagram
    Order }|..|{ Customer
```

**Relationship Notation:**
- First marker: `}|` (many), `||` (one), `o|` (zero or one)
- Relationship line: `--` (identifying), `..` (non-identifying)
- Second marker: `|{` (many), `||` (one), `|o` (zero or one)

---

## Gantt Charts

### ❌ Error 24: Reserved Words as Task Names

**Severity:** 🔴 Critical

**Problem:** Words like "gantt", "section", "dateFormat" cause errors.

**Incorrect:**

```mermaid
gantt
    dateFormat YYYY-MM-DD
    section Section
    gantt : active, 2021-04-03, 1d
    section : 2021-04-04, 1d
```

**Correct:**

```mermaid
gantt
    dateFormat YYYY-MM-DD
    section Section
    "gantt task" : active, 2021-04-03, 1d
    "section task" : 2021-04-04, 1d
```

**Reserved Gantt Keywords:**
- `gantt`, `section`, `dateFormat`, `click`, `title`
- `axisFormat`, `excludes`, `includes`, `todayMarker`, `topAxis`

---

### ❌ Error 25: Missing Comma in Date Specification

**Severity:** 🟠 High - Browser-dependent (fails in Firefox)

**Problem:** Missing comma between task ID and date.

**Incorrect:**

```mermaid
gantt
    dateFormat YYYY-MM-DD
    Fake Event: fake 2022-11-16, 10d
```

**Correct:**

```mermaid
gantt
    dateFormat YYYY-MM-DD
    Fake Event: fake, 2022-11-16, 10d
```

**Error Message (Firefox):** `Invalid date:fake 2022-11-16`

---

### ❌ Error 26: Special Characters in Task Names

**Severity:** 🟠 High

**Problem:** Hash, semicolon, or colon cause truncation or errors.

**Incorrect:**

```mermaid
gantt
    section Tasks
    Task#1 : 2024-01-01, 3d
    Task;2 : 2024-01-04, 2d
    Task:3 : 2024-01-06, 1d
```

**Correct:**

```mermaid
gantt
    section Tasks
    Task 1 : 2024-01-01, 3d
    Task 2 : 2024-01-04, 2d
    Task 3 : 2024-01-06, 1d
```

**Characters to Avoid in Gantt:**
- `#` causes truncation
- `;` causes syntax errors
- `:` at beginning/end causes errors

---

### ❌ Error 27: Incorrect After Dependency Syntax

**Severity:** 🟡 Medium

**Problem:** Missing or incorrect "after" keyword for dependencies.

**Incorrect:**

```mermaid
gantt
    dateFormat YYYY-MM-DD
    VM : ps2, 2w
    Config OS : ps2, 1w
```

**Correct:**

```mermaid
gantt
    dateFormat YYYY-MM-DD
    VM : ps2, 2020-06-01, 2w
    Config OS : after ps2, 1w
```

---

## Pie Charts

### ❌ Error 28: Non-Positive Values

**Severity:** 🟠 High - Silent failure

**Problem:** Negative numbers or non-numeric values.

**Incorrect:**

```mermaid
pie
    title Key elements
    "Calcium" : aa
    "Potassium" : -12
    "Magnesium" :
```

**Correct:**

```mermaid
pie
    title Key elements
    "Calcium" : 40
    "Potassium" : 50
    "Magnesium" : 10
```

**Note:** Pie charts fail silently without helpful error messages for this issue.

---

## General Resources

### Official Documentation

- **Mermaid Official Docs:** <https://mermaid.js.org/>
- **Mermaid Live Editor:** <https://mermaid.live/>
- **GitHub Repository:** <https://github.com/mermaid-js/mermaid>

### Diagram-Specific Guides

- [Activity Diagrams Guide](diagrams/activity-diagrams.md)
- [Deployment Diagrams Guide](diagrams/deployment-diagrams.md)
- [Architecture Diagrams Guide](diagrams/architecture-diagrams.md)
- [Sequence Diagrams Guide](diagrams/sequence-diagrams.md)
- [Unicode Symbols Guide](unicode-symbols/guide.md)

### Validation Tools

**Command Line:**

```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Validate and convert
mmdc -i input.mmd -o output.png
```

**Python Scripts (This Skill):**

```bash
# Validate diagrams in markdown
python scripts/extract_mermaid.py file.md --validate

# Convert to image
python scripts/mermaid_to_image.py diagram.mmd output.png
```

### Debugging Tips

1. **Test in Mermaid Live Editor** - Fastest way to validate syntax
2. **Check Mermaid Version** - Some syntax is version-specific
3. **Look for Reserved Words** - Wrap suspicious words in quotes
4. **Simplify First** - Strip down to minimal example, then add back
5. **Check Browser Console** - Error messages appear in dev tools
6. **Use Validation Scripts** - Automated checking catches common errors

---

## Error Severity Legend

- 🔴 **Critical** - Causes immediate parse failure, diagram won't render
- 🟠 **High** - Major visual issues or unexpected behavior
- 🟡 **Medium** - Minor visual issues or warnings
- 🟢 **Low** - Best practice violations, but diagram still renders

---

**Version:** 1.0
**Last Updated:** 2025-01-13
**Total Errors Documented:** 28
**Research Sources:** GitHub Issues (mermaid-js/mermaid), Stack Overflow, Mermaid Official Docs, Community Forums
