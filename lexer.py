#!/usr/bin/env python3

class TokenType:
    """Token types for the SQL-like language"""
    # Keywords
    SELECT = "SELECT"
    FROM = "FROM"
    WHERE = "WHERE"
    INSERT = "INSERT"
    INTO = "INTO"
    VALUES = "VALUES"
    UPDATE = "UPDATE"
    SET = "SET"
    DELETE = "DELETE"
    CREATE = "CREATE"
    TABLE = "TABLE"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    
    # Types
    INT = "INT"
    FLOAT = "FLOAT"
    TEXT = "TEXT"
    
    # Identifiers
    IDENTIFIER = "IDENTIFIER"
    
    # Literals
    NUMBER = "NUMBER"
    STRING = "STRING"
    
    # Operators
    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    LESS_THAN = "LESS_THAN"
    GREATER_THAN = "GREATER_THAN"
    LESS_EQUAL = "LESS_EQUAL"
    GREATER_EQUAL = "GREATER_EQUAL"
    PLUS = "PLUS"
    MINUS = "MINUS"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    
    # Delimiters/Punctuation
    LEFT_PAREN = "LPAR"
    RIGHT_PAREN = "RPAR"
    COMMA = "COMMA"
    SEMICOLON = "SEMICOLON"
    
    # EOF
    EOF = "EOF"


class Token:
    """Represents a token with its type and lexeme"""
    def __init__(self, tokenType, lexeme, line, col):
        self.tokenType = tokenType
        self.lexeme = lexeme
        self.line = line
        self.col = col
    
    def __str__(self):
        return f"Token: {self.tokenType}, Lexeme: {self.lexeme}"


class LexerError(Exception):
    """Custom exception for lexical errors"""
    def __init__(self, message, line, col):
        self.message = message
        self.line = line
        self.col = col
        super().__init__(f"Error: {message} at line {line}, position {col}.")


class Lexer:
    """Lexical analyzer for SQL-like language"""
    
    def __init__(self, source):
        self.source = source
        self.currentPos = 0
        self.currentLine = 1
        self.currentCol = 1
        self.tokens = []
        self.errors = []  # Collect all errors instead of raising immediately
        
        # Keywords
        self.keywords = {
            'SELECT': TokenType.SELECT,
            'FROM': TokenType.FROM,
            'WHERE': TokenType.WHERE,
            'INSERT': TokenType.INSERT,
            'INTO': TokenType.INTO,
            'VALUES': TokenType.VALUES,
            'UPDATE': TokenType.UPDATE,
            'SET': TokenType.SET,
            'DELETE': TokenType.DELETE,
            'CREATE': TokenType.CREATE,
            'TABLE': TokenType.TABLE,
            'INT': TokenType.INT,
            'FLOAT': TokenType.FLOAT,
            'TEXT': TokenType.TEXT,
            'AND': TokenType.AND,
            'OR': TokenType.OR,
            'NOT': TokenType.NOT
        }

    def currentChar(self):
        """Get current character"""
        if self.currentPos >= len(self.source):
            return None
        return self.source[self.currentPos]
    
    def peekChar(self, offset=1):
        """Peek at character ahead"""
        pos = self.currentPos + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]
    
    def advance(self):
        """Advance to next character"""
        if self.currentChar() == '\n':
            self.currentLine += 1
            self.currentCol = 1
        else:
            self.currentCol += 1
        self.currentPos += 1
    
    def skipWhitespace(self):
        """Skip whitespace characters"""
        while self.currentChar() and self.currentChar().isspace():
            self.advance()
    
    def tokenize(self):
        """Tokenize the entire source"""
        while self.currentPos < len(self.source):
            self.skipWhitespace()
            if self.currentPos >= len(self.source):
                break
            
            try:
                token = self.nextToken()
                if token:
                    self.tokens.append(token)
            except LexerError as e:
                # Collect error instead of raising
                self.errors.append(e)
                # Error recovery: skip the problematic character and continue
                if self.currentPos < len(self.source):
                    self.advance()
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, "", self.currentLine, self.currentCol))
        return self.tokens
    
    def getErrors(self):
        """Get all collected errors"""
        return self.errors
    
    def nextToken(self):
        """Get next token"""
        char = self.currentChar()
        startCol = self.currentCol
        
        # String literal
        if char == "'":
            return self.tokenizeString()
        
        # Single-line comment
        if char == '-' and self.peekChar() == '-':
            self.skipSingleLineComment()
            return None

        # Multi-line comment
        if char == '#':
            return self.tokenizeMultilineComment()
        
        # Numbers
        if char.isdigit():
            return self.tokenizeNumber()
        
        # Identifiers and keywords
        if char.isalpha():
            return self.tokenizeIdentifierOrKeyword()
        
        # Operators and delimiters
        return self.tokenizeSymbol()
    
    def tokenizeString(self):
        """Tokenize string literal"""
        startLine = self.currentLine
        startCol = self.currentCol
        lexeme = "'"
        self.advance()  # Skip opening quote
        
        while self.currentChar():
            if self.currentChar() == "'":
                lexeme += "'"
                self.advance()
                return Token(TokenType.STRING, lexeme, startLine, startCol)
            
            if self.currentChar() == '\n':
                raise LexerError("unclosed string", startLine, startCol)
            
            lexeme += self.currentChar()
            self.advance()
        
        raise LexerError("unclosed string", startLine, startCol)
    
    def skipSingleLineComment(self):
        """Skip single-line comment starting with --"""
        while self.currentChar() and self.currentChar() != '\n':
            self.advance()
    
    def tokenizeMultilineComment(self):
        """Tokenize multi-line comment starting with # (can be # or ##)"""
        startLine = self.currentLine
        startCol = self.currentCol
        
        # Look for ## (multi-line comment style)
        if self.currentChar() == '#' and self.peekChar() == '#':
            # ## style comment
            self.advance()  # Skip second #
            self.skipMultilineComment()
        else:
            # Single # - treat as invalid according to spec
            raise LexerError(f"invalid character '#'", startLine, startCol)
        
        return None
    
    def skipMultilineComment(self):
        """Skip multiline comment from ## to ##"""
        # Look for the closing ##
        while self.currentChar():
            if self.currentChar() == '#':
                self.advance()
                if self.currentChar() == '#':
                    # Found closing ##
                    self.advance()  # Skip closing #
                    return
            else:
                self.advance()
        
        raise LexerError("unclosed comment", self.currentLine, self.currentCol)
    
    def tokenizeNumber(self):
        """Tokenize numeric literal"""
        startCol = self.currentCol
        lexeme = ""
        
        # Integer part
        while self.currentChar() and self.currentChar().isdigit():
            lexeme += self.currentChar()
            self.advance()
        
        # Check for decimal point
        if self.currentChar() == '.':
            lexeme += '.'
            self.advance()
            
            # Fractional part
            if self.currentChar() and self.currentChar().isdigit():
                while self.currentChar() and self.currentChar().isdigit():
                    lexeme += self.currentChar()
                    self.advance()
            else:
                # Just a dot, could be part of something else
                # Actually, let's treat it as invalid
                pass
        
        return Token(TokenType.NUMBER, lexeme, self.currentLine, startCol)
    
    def tokenizeIdentifierOrKeyword(self):
        """Tokenize identifier or keyword"""
        startCol = self.currentCol
        lexeme = ""
        
        while self.currentChar() and (self.currentChar().isalnum() or self.currentChar() == '_'):
            lexeme += self.currentChar()
            self.advance()
        
        # Check if it's a keyword
        tokenType = self.keywords.get(lexeme, TokenType.IDENTIFIER)
        return Token(tokenType, lexeme, self.currentLine, startCol)
    
    def tokenizeSymbol(self):
        """Tokenize operators and delimiters"""
        startCol = self.currentCol
        char = self.currentChar()
        
        # Single character tokens
        singleCharTokens = {
            '(': TokenType.LEFT_PAREN,
            ')': TokenType.RIGHT_PAREN,
            ',': TokenType.COMMA,
            ';': TokenType.SEMICOLON,
            '+': TokenType.PLUS,
            '-': TokenType.MINUS,
            '*': TokenType.MULTIPLY,
            '/': TokenType.DIVIDE
        }
        
        if char in singleCharTokens:
            self.advance()
            return Token(singleCharTokens[char], char, self.currentLine, startCol)
        
        # Two character tokens
        if char == '=':
            self.advance()
            return Token(TokenType.EQUAL, "=", self.currentLine, startCol)
        
        if char == '!':
            self.advance()
            if self.currentChar() == '=':
                self.advance()
                return Token(TokenType.NOT_EQUAL, "!=", self.currentLine, startCol)
            else:
                raise LexerError(f"invalid character '{char}'", self.currentLine, startCol)
        
        if char == '<':
            self.advance()
            if self.currentChar() == '=':
                self.advance()
                return Token(TokenType.LESS_EQUAL, "<=", self.currentLine, startCol)
            return Token(TokenType.LESS_THAN, "<", self.currentLine, startCol)
        
        if char == '>':
            self.advance()
            if self.currentChar() == '=':
                self.advance()
                return Token(TokenType.GREATER_EQUAL, ">=", self.currentLine, startCol)
            return Token(TokenType.GREATER_THAN, ">", self.currentLine, startCol)
        
        # Unknown character
        raise LexerError(f"invalid character '{char}'", self.currentLine, startCol)


def main():
    """Main function to run the lexer"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python lexer.py <input_file>")
        sys.exit(1)
    
    inputFile = sys.argv[1]
    
    try:
        with open(inputFile, 'r') as f:
            source = f.read()
        
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        # Print tokens
        for token in tokens:
            if token.tokenType != TokenType.EOF:
                print(f"Token: {token.tokenType}, Lexeme: {token.lexeme}")
    
    except FileNotFoundError:
        print(f"Error: File '{inputFile}' not found.")
        sys.exit(1)
    except LexerError as e:
        print(f"Error: {e.message} at line {e.line}, position {e.col}.")
        sys.exit(1)


if __name__ == "__main__":
    main()