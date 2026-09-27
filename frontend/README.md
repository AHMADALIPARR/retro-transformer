# frontend — COBOL parser (Agent 1)

Hand-rolled COBOL-85 lexer + parser, stdlib only. Emits the IR
documented in `../IR_SCHEMA.md`.

```
frontend/
  lexer.py          fixed-format normalization, comments, tokenization
  parser.py         divisions/sections/paragraphs/statements -> IR dict
  ir.py             JSON emit/load helpers
  __main__.py       CLI: python -m frontend <file.cbl> [out.json]
  test_frontend.py  fixture tests (plain asserts)
```

Run the tests from the repo root:

```sh
python3 frontend/test_frontend.py
```

Parse one file:

```sh
python3 -m frontend fixtures/hello.cbl
```
