# IR Schema — retro transformer

The COBOL frontend (`frontend/`) parses COBOL-85 source into a JSON
Intermediate Representation. Every consumer (engine, pipeline, deploy)
reads this shape and nothing else.

## Top-level shape

```json
{
  "program": "NAME",
  "divisions": [
    {
      "name": "IDENTIFICATION",
      "sections": [
        {
          "name": "MAIN",
          "paragraphs": [
            {
              "name": "MAIN-LOGIC",
              "statements": [
                {"type": "DISPLAY", "text": "DISPLAY 'HELLO'", "line": 42}
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

## Fields

| Level | Key | Meaning |
|---|---|---|
| root | `program` | Value of the `PROGRAM-ID` paragraph, else `"UNKNOWN"` |
| root | `divisions` | In source order: `IDENTIFICATION`, `ENVIRONMENT`, `DATA`, `PROCEDURE` |
| division | `name` | Division name, uppercase |
| division | `sections` | `SECTION.` headers; divisions without one get a single `"MAIN"` section |
| section | `name` | Section name, uppercase (`"MAIN"` when implicit) |
| section | `paragraphs` | Paragraphs in source order |
| paragraph | `name` | Paragraph label as written (`MAIN-LOGIC`), or `01 PAY-RECORD` / `FD PAY-FILE` in the DATA division |
| paragraph | `statements` | Statements in source order |
| statement | `type` | Uppercase verb keyword (see below) |
| statement | `text` | Full original statement text, exactly as written, minus the terminating period |
| statement | `line` | 1-based source line where the statement starts |

## Statement types

`type` is the uppercase verb that opens the statement:

`DISPLAY` `MOVE` `ADD` `SUBTRACT` `MULTIPLY` `DIVIDE` `COMPUTE`
`IF` `ELSE` `PERFORM` `OPEN` `READ` `WRITE` `CLOSE` `CALL` `COPY`
`ACCEPT` `EVALUATE` `CONTINUE` `EXIT` `STOP`
`END-IF` `END-PERFORM` `END-READ` `END-WRITE` `END-EVALUATE` …

Plus three special types:

| Type | When |
|---|---|
| `GO TO` | `GO TO para.` (two-word verb, kept together) |
| `CLAUSE` | A non-verb line: `PROGRAM-ID` value, `SELECT … ASSIGN TO …`, etc. |
| `DATA` | A data-description line in the DATA division (`01 PAY-RECORD.`, `05 EMP-NAME PIC X(20).`) |

## Structural rules

1. **Flat statements.** The token stream is split at every verb
   keyword, so `IF` / `ELSE` / `END-IF` appear as *sibling* statements
   in source order, not nested. Scope is recoverable from the
   `END-*` markers.
2. **DATA division.** Each `01`/`77`-level record (and each `FD`/`SD`)
   opens a paragraph named e.g. `"01 PAY-RECORD"`; every
   data-description line under it is a `DATA` statement.
3. **Paragraphs** are only recognized in `PROCEDURE` division
   (`NAME.` lines) plus the fixed header keywords elsewhere
   (`PROGRAM-ID`, `AUTHOR`, `FILE-CONTROL`, …).
4. **`line`** is always the statement's first source line, 1-based.
5. **Comments** (`*>`, `*`/`/` in column 7) and sequence-number areas
   are stripped before parsing; continuations (`-` in column 7) are
   joined.

## Known limitations

- One verb-looking word always starts a new statement, so a data item
  literally named `DISPLAY` would split a statement. Don't do that.
- `EVALUATE … WHEN … END-EVALUATE` flattens like `IF`.
- No `COPY` book expansion, no `REPLACING`, no nested programs.
- Decimal literals (`3.14`) are safe; a period is only a terminator
  when it stands alone as its own token.
