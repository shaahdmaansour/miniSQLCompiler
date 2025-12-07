# miniSQLCompiler

This project implements a lexical analyzer (scanner) for a SQL-like language as part of CSCI415 - Compiler Design.

## Features

- **Case-sensitive** tokenization
- **Keywords**: SELECT, FROM, WHERE, INSERT, INTO, VALUES, UPDATE, SET, DELETE, CREATE, TABLE, INT, FLOAT, TEXT, AND, OR, NOT
- **Identifiers**: User-defined names starting with a letter and containing letters, digits, or underscores
- **Literals**: String (enclosed in single quotes) and numeric constants
- **Operators**: Arithmetic (`+`, `-`, `*`, `/`) and comparison (`=`, `!=`, `<`, `>`, `<=`, `>=`)
- **Comments**: Single-line (`--`) and multi-line (`##...##`)
- **Error Detection**: Invalid characters, unclosed strings, unclosed comments with accurate position reporting

## Files

- `lexer.py` - Main lexical analyzer implementation
- `input.txt` - Sample input file with SQL-like statements
- `report.md` - Detailed report on implementation

## Usage

Run the lexer with a text file containing SQL-like statements:

```bash
python lexer.py input.txt
```

The output displays each token with its type and lexeme.

## Example Input

```sql
-- This is a comment
CREATE TABLE students (id INT, name TEXT);
INSERT INTO students VALUES (1, 'Ali');
SELECT name FROM students WHERE id = 1;
```

## Example Output

```
Token: CREATE, Lexeme: CREATE
Token: TABLE, Lexeme: TABLE
Token: IDENTIFIER, Lexeme: students
Token: LEFT_PAREN, Lexeme: (
Token: IDENTIFIER, Lexeme: id
Token: INT, Lexeme: INT
Token: COMMA, Lexeme: ,
Token: IDENTIFIER, Lexeme: name
Token: TEXT, Lexeme: TEXT
Token: RIGHT_PAREN, Lexeme: )
Token: SEMICOLON, Lexeme: ;
Token: INSERT, Lexeme: INSERT
Token: INTO, Lexeme: INTO
Token: IDENTIFIER, Lexeme: students
Token: VALUES, Lexeme: VALUES
Token: LEFT_PAREN, Lexeme: (
Token: NUMBER, Lexeme: 1
Token: COMMA, Lexeme: ,
Token: STRING, Lexeme: 'Ali'
Token: RIGHT_PAREN, Lexeme: )
Token: SEMICOLON, Lexeme: ;
Token: SELECT, Lexeme: SELECT
Token: IDENTIFIER, Lexeme: name
Token: FROM, Lexeme: FROM
Token: IDENTIFIER, Lexeme: students
Token: WHERE, Lexeme: WHERE
Token: IDENTIFIER, Lexeme: id
Token: EQUAL, Lexeme: =
Token: NUMBER, Lexeme: 1
Token: SEMICOLON, Lexeme: ;
```

## Error Handling

The lexer detects and reports lexical errors with accurate line and column positions:

- **Invalid characters**: `Error: invalid character '@' at line 3, position 5.`
- **Unclosed strings**: `Error: unclosed string at line 2, position 15.`
- **Unclosed comments**: `Error: unclosed comment at line 5, position 1.`

## Testing

The implementation has been tested with various SQL-like statements including:
- CREATE TABLE statements
- INSERT statements
- SELECT queries with WHERE clauses
- UPDATE statements
- DELETE statements
- Comments (both single-line and multi-line)
- Error cases (invalid characters, unclosed strings, etc.)

All tests passed successfully.

## Requirements

- Python 3.x

## Author

Phase 01 - Lexical Analyzer Implementation