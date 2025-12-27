# miniSQLCompiler

A complete SQL-like language compiler implementation featuring Lexical Analysis (Phase 01), Syntax Analysis (Phase 02), and Semantic Analysis (Phase 03). This project is part of CSCI415 - Compiler Design.

## Project Overview

This compiler processes SQL-like queries through three main phases:
1. **Lexical Analysis** - Tokenizes input source code
2. **Syntax Analysis** - Builds parse trees using recursive descent parsing
3. **Semantic Analysis** - Validates semantic correctness and manages symbol tables

## Features

### Phase 01 - Lexical Analyzer
- **Case-sensitive** tokenization
- **Keywords**: SELECT, FROM, WHERE, INSERT, INTO, VALUES, UPDATE, SET, DELETE, CREATE, TABLE, INT, FLOAT, TEXT, AND, OR, NOT
- **Identifiers**: User-defined names starting with a letter and containing letters, digits, or underscores
- **Literals**: String (enclosed in single quotes) and numeric constants
- **Operators**: Arithmetic (`+`, `-`, `*`, `/`) and comparison (`=`, `!=`, `<`, `>`, `<=`, `>=`)
- **Comments**: Single-line (`--`) and multi-line (`##...##`)
- **Error Detection**: Invalid characters, unclosed strings, unclosed comments with accurate position reporting

### Phase 02 - Syntax Analyzer
- **Recursive Descent Parser** with parse tree generation
- **Grammar Support**:
  - CREATE TABLE statements
  - INSERT INTO statements
  - SELECT queries with WHERE clauses
  - UPDATE statements
  - DELETE statements
- **Error Recovery**: Panic mode error recovery with synchronizing tokens
- **Parse Tree Output**: Hierarchical tree structure showing statement structure

### Phase 03 - Semantic Analyzer
- **Symbol Table Management**: Hierarchical structure storing table and column metadata
- **Identifier Verification**:
  - Table existence checks
  - Column existence checks
  - Redeclaration prevention
  - Ambiguity checking (infrastructure ready for multi-table queries)
- **Type Checking**:
  - Creation data types validation (INT, FLOAT, TEXT)
  - Insertion type consistency (INSERT INTO)
  - Comparison type compatibility (WHERE clause)
- **Output**:
  - Symbol table dump
  - Annotated parse tree with data types and semantic links
  - Detailed error messages with line and column numbers

## Files

### Core Implementation
- `lexer.py` - Lexical analyzer (Phase 01)
- `parser.py` - Syntax analyzer with parse tree generation (Phase 02)
- `semanticAnalyzer.py` - Semantic analyzer with symbol table management (Phase 03)

### GUI Application
- `gui.py` - Flask-based web interface
- `gui/index.html` - Frontend HTML
- `gui/script.js` - Frontend JavaScript
- `gui/style.css` - Styling

### Test Files
- `test/input.txt` - Basic test cases
- `test/inputTwo.txt` - Additional test cases
- `test/inputThree.txt` - Expression testing
- `test/inputFour.txt` - Error cases
- `test/inputFive.txt` - Ambiguity checking examples

### Configuration
- `requirements.txt` - Python dependencies

## Usage

### Command Line

#### Lexical Analysis Only
```bash
python lexer.py test/input.txt
```

#### Syntax Analysis (includes lexical analysis)
```bash
python parser.py test/input.txt
```

#### Semantic Analysis (includes lexical and syntax analysis)
```python
from lexer import Lexer
from parser import Parser
from semanticAnalyzer import SemanticAnalyzer

# Read input
with open('test/input.txt', 'r') as f:
    code = f.read()

# Phase 1: Tokenize
lexer = Lexer(code)
tokens = lexer.tokenize()

# Phase 2: Parse
parser = Parser(tokens)
parseTree = parser.parse()

# Phase 3: Semantic Analysis
analyzer = SemanticAnalyzer(parseTree)
success = analyzer.analyze()

if success:
    print("Semantic Analysis Successful!")
    print(analyzer.getSymbolTable())
else:
    for error in analyzer.getErrors():
        print(f"Error: {error.message} at line {error.line}, col {error.col}")
```

### Web GUI

Start the Flask server:
```bash
python gui.py
```

Then open your browser and navigate to:
```
http://localhost:5001
```

The GUI provides:
- **Tokenize Tab**: View tokens in detailed or general mode
- **Parse Tab**: View parse tree structure
- **Analyze Tab**: View semantic analysis results including symbol table and annotated parse tree

## Example Input

```sql
-- This is a comment
CREATE TABLE students (id INT, name TEXT, score FLOAT);
INSERT INTO students VALUES (1, 'Ali', 95.5);
SELECT name FROM students WHERE id = 1;
UPDATE students SET score = 98.0 WHERE id = 1;
DELETE FROM students WHERE score < 50.0;
```

## Example Output

### Lexical Analysis
```
Token: CREATE, Lexeme: CREATE
Token: TABLE, Lexeme: TABLE
Token: IDENTIFIER, Lexeme: students
Token: LEFT_PAREN, Lexeme: (
Token: IDENTIFIER, Lexeme: id
Token: INT, Lexeme: INT
...
```

### Syntax Analysis
```
Query
  CreateStmt
    CREATE
    TABLE
    IDENTIFIER [students]
    LEFT_PAREN
    ColumnList
      ColumnDef
        IDENTIFIER [id]
        Type
          INT
      ...
```

### Semantic Analysis
```
Semantic Analysis Successful. Query is valid.

Symbol Table:
  Table: students
    - id: INT
    - name: TEXT
    - score: FLOAT

Annotated Parse Tree:
  Query
    CreateStmt
      IDENTIFIER [students] → students
      ColumnDef
        IDENTIFIER [id] <INT> → students.id
        Type
          INT
    ...
```

## Error Handling

### Lexical Errors
- **Invalid characters**: `Error: invalid character '@' at line 3, position 5.`
- **Unclosed strings**: `Error: unclosed string at line 2, position 15.`
- **Unclosed comments**: `Error: unclosed comment at line 5, position 1.`

### Syntax Errors
- **Missing tokens**: `Syntax Error: Expected 'FROM' at line 5, position 10. Expected 'FROM', but found 'WHERE'.`
- **Unexpected tokens**: `Syntax Error: Unexpected token at line 3, position 15.`

### Semantic Errors
- **Table not found**: `Semantic Error: Table 'users' does not exist at line 7, position 13.`
- **Column not found**: `Semantic Error: Column 'age' does not exist in table 'students' at line 8, position 8.`
- **Type mismatch**: `Semantic Error: Type mismatch: Column 'id' is defined as INT, but a STRING literal was provided for insertion at line 5, position 20.`
- **Ambiguity**: `Semantic Error: Column 'name' is ambiguous: it exists in multiple tables (students, teachers). Use table.column format to disambiguate.`

## Testing

The implementation has been tested with various SQL-like statements including:
- CREATE TABLE statements with multiple columns
- INSERT statements with type validation
- SELECT queries with WHERE clauses and expressions
- UPDATE statements with assignments
- DELETE statements with conditions
- Complex WHERE clauses with AND, OR, NOT operators
- Arithmetic expressions in SELECT and WHERE clauses
- Comments (both single-line and multi-line)
- Error cases (invalid syntax, type mismatches, missing tables/columns)

All test files in the `test/` directory pass successfully.

## Requirements

- Python 3.x
- Flask (for GUI) - install with `pip install -r requirements.txt`

## Project Structure

```
miniSQLCompiler/
├── lexer.py              # Phase 01: Lexical Analyzer
├── parser.py              # Phase 02: Syntax Analyzer
├── semanticAnalyzer.py    # Phase 03: Semantic Analyzer
├── gui.py                 # Web GUI application
├── gui/                   # GUI frontend files
│   ├── index.html
│   ├── script.js
│   └── style.css
├── test/                  # Test input files
│   ├── input.txt
│   ├── inputTwo.txt
│   ├── inputThree.txt
│   ├── inputFour.txt
│   └── inputFive.txt
└── README.md
```

## Phase Implementation Status

- ✅ **Phase 01 - Lexical Analysis**: Complete
- ✅ **Phase 02 - Syntax Analysis**: Complete
- ✅ **Phase 03 - Semantic Analysis**: Complete

## Author

CSCI415 - Compiler Design Project
- Phase 01: Lexical Analyzer Implementation
- Phase 02: Syntax Analyzer with Parse Tree Generation
- Phase 03: Semantic Analyzer with Symbol Table Management