#!/usr/bin/env python3
"""
Syntax Analyzer (Parser) for SQL-like language
Implements Recursive Descent Parsing with Parse Tree generation
"""

from lexer import Token, TokenType, Lexer


class ParseTreeNode:
    """Base class for all parse tree nodes"""
    def __init__(self, nodeType, children=None, token=None):
        self.nodeType = nodeType
        self.children = children if children is not None else []
        self.token = token  # Terminal nodes may have associated token
    
    def addChild(self, child):
        """Add a child node"""
        if child is not None:
            self.children.append(child)
    
    def toDict(self):
        """Convert parse tree node to dictionary for JSON serialization"""
        result = {
            'nodeType': self.nodeType,
            'children': [child.toDict() if hasattr(child, 'toDict') else str(child) for child in self.children]
        }
        if self.token:
            result['token'] = {
                'type': self.token.tokenType,
                'lexeme': self.token.lexeme,
                'line': self.token.line,
                'col': self.token.col
            }
        return result
    
    def __str__(self, level=0):
        """String representation of the parse tree"""
        indent = "  " * level
        result = f"{indent}{self.nodeType}"
        if self.token:
            result += f" [{self.token.lexeme}]"
        result += "\n"
        for child in self.children:
            result += child.__str__(level + 1)
        return result


class ParserError(Exception):
    """Custom exception for syntax errors"""
    def __init__(self, message, line, col, expected=None, found=None):
        self.message = message
        self.line = line
        self.col = col
        self.expected = expected
        self.found = found
        errorMsg = f"Syntax Error: {message} at line {line}, position {col}"
        if expected and found:
            errorMsg += f". Expected '{expected}', but found '{found}'."
        super().__init__(errorMsg)


class Parser:
    """Recursive Descent Parser for SQL-like language"""
    
    def __init__(self, tokens):
        self.tokens = tokens
        self.currentIndex = 0
        self.errors = []
        self.syncTokens = {
            TokenType.SEMICOLON,
            TokenType.CREATE,
            TokenType.INSERT,
            TokenType.SELECT,
            TokenType.UPDATE,
            TokenType.DELETE,
            TokenType.EOF
        }
    
    def currentToken(self):
        """Get current token"""
        if self.currentIndex >= len(self.tokens):
            return self.tokens[-1] if self.tokens else None
        return self.tokens[self.currentIndex]
    
    def peekToken(self, offset=1):
        """Peek at token ahead"""
        idx = self.currentIndex + offset
        if idx >= len(self.tokens):
            return self.tokens[-1] if self.tokens else None
        return self.tokens[idx]
    
    def advance(self):
        """Advance to next token"""
        if self.currentIndex < len(self.tokens):
            self.currentIndex += 1
    
    def match(self, tokenType):
        """Check if current token matches expected type"""
        if self.currentToken() and self.currentToken().tokenType == tokenType:
            return True
        return False
    
    def consume(self, tokenType, errorMsg=None):
        """Consume token of expected type or raise error"""
        if self.match(tokenType):
            token = self.currentToken()
            self.advance()
            return token
        
        # Error handling
        current = self.currentToken()
        if current:
            expected = errorMsg if errorMsg else tokenType
            found = current.lexeme if current.lexeme else current.tokenType
            error = ParserError(
                errorMsg if errorMsg else f"Expected {tokenType}",
                current.line,
                current.col,
                expected=expected,
                found=found
            )
            self.errors.append(error)
            raise error
        else:
            error = ParserError(
                errorMsg if errorMsg else f"Expected {tokenType}",
                0, 0,
                expected=errorMsg if errorMsg else tokenType,
                found="EOF"
            )
            self.errors.append(error)
            raise error
    
    def errorRecovery(self, error):
        """Panic mode error recovery"""
        # Skip tokens until we find a synchronizing token
        startIndex = self.currentIndex
        
        # If we're already at a sync token (except SEMICOLON), advance past it
        if self.currentToken() and self.currentToken().tokenType in self.syncTokens:
            if self.currentToken().tokenType != TokenType.SEMICOLON:
                self.advance()
            return
        
        # Skip tokens until we find a synchronizing token
        while self.currentToken() and self.currentToken().tokenType != TokenType.EOF:
            currentType = self.currentToken().tokenType
            
            # If we find a semicolon, advance past it and stop (ready for next statement)
            if currentType == TokenType.SEMICOLON:
                self.advance()
                return
            
            # If we find a statement keyword, stop here (ready to parse it)
            if currentType in {TokenType.CREATE, TokenType.INSERT, TokenType.SELECT, 
                              TokenType.UPDATE, TokenType.DELETE}:
                return
            
            self.advance()
        
        # Safety: ensure we always advance at least one token
        if self.currentIndex == startIndex and self.currentToken():
            self.advance()
    
    def parse(self):
        """Parse the entire token stream"""
        root = ParseTreeNode("Query")
        maxErrors = 100  # Prevent infinite loops
        errorCount = 0
        consecutiveErrors = 0  # Track consecutive errors to detect stuck state
        
        while self.currentToken() and self.currentToken().tokenType != TokenType.EOF:
            if errorCount >= maxErrors:
                # Too many errors, stop parsing
                break
            
            previousIndex = self.currentIndex
            try:
                stmt = self.parseStatement()
                if stmt:
                    root.addChild(stmt)
                # Reset error count on successful parse
                errorCount = 0
                consecutiveErrors = 0
            except ParserError as e:
                errorCount += 1
                consecutiveErrors += 1
                
                # If we're stuck (same position after recovery), try harder recovery
                if consecutiveErrors > 3:
                    # More aggressive recovery: skip to next semicolon or statement
                    while self.currentToken() and self.currentToken().tokenType != TokenType.EOF:
                        if self.currentToken().tokenType == TokenType.SEMICOLON:
                            self.advance()
                            consecutiveErrors = 0
                            break
                        elif self.currentToken().tokenType in {TokenType.CREATE, TokenType.INSERT, 
                                                               TokenType.SELECT, TokenType.UPDATE, TokenType.DELETE}:
                            consecutiveErrors = 0
                            break
                        self.advance()
                
                self.errorRecovery(e)
                
                # Safety check: if we didn't advance, force advance to prevent infinite loop
                if self.currentIndex == previousIndex and self.currentToken():
                    self.advance()
                
                # Continue parsing after recovery
                continue
        
        return root
    
    def parseStatement(self):
        """Statement → CreateStmt SEMICOLON | InsertStmt SEMICOLON | SelectStmt SEMICOLON | UpdateStmt SEMICOLON | DeleteStmt SEMICOLON"""
        stmtNode = None
        
        if self.match(TokenType.CREATE):
            stmtNode = self.parseCreateStatement()
        elif self.match(TokenType.INSERT):
            stmtNode = self.parseInsertStatement()
        elif self.match(TokenType.SELECT):
            stmtNode = self.parseSelectStatement()
        elif self.match(TokenType.UPDATE):
            stmtNode = self.parseUpdateStatement()
        elif self.match(TokenType.DELETE):
            stmtNode = self.parseDeleteStatement()
        else:
            current = self.currentToken()
            if current:
                raise ParserError(
                    "Expected statement keyword (CREATE, INSERT, SELECT, UPDATE, DELETE)",
                    current.line,
                    current.col,
                    expected="CREATE, INSERT, SELECT, UPDATE, or DELETE",
                    found=current.lexeme if current.lexeme else current.tokenType
                )
            else:
                raise ParserError(
                    "Expected statement keyword",
                    0, 0,
                    expected="CREATE, INSERT, SELECT, UPDATE, or DELETE",
                    found="EOF"
                )
        
        # Consume semicolon
        try:
            self.consume(TokenType.SEMICOLON, "Expected ';'")
        except ParserError:
            pass  # Error already recorded
        
        return stmtNode
    
    def parseCreateStatement(self):
        """CreateStmt → CREATE TABLE IDENTIFIER LEFT_PAREN ColumnList RIGHT_PAREN"""
        node = ParseTreeNode("CreateStmt")
        
        # CREATE
        createToken = self.consume(TokenType.CREATE, "Expected 'CREATE'")
        node.addChild(ParseTreeNode("CREATE", token=createToken))
        
        # TABLE
        tableToken = self.consume(TokenType.TABLE, "Expected 'TABLE'")
        node.addChild(ParseTreeNode("TABLE", token=tableToken))
        
        # IDENTIFIER (table name)
        idToken = self.consume(TokenType.IDENTIFIER, "Expected table name")
        node.addChild(ParseTreeNode("IDENTIFIER", token=idToken))
        
        # LEFT_PAREN
        lparenToken = self.consume(TokenType.LEFT_PAREN, "Expected '('")
        node.addChild(ParseTreeNode("LEFT_PAREN", token=lparenToken))
        
        # ColumnList
        columnList = self.parseColumnList()
        node.addChild(columnList)
        
        # RIGHT_PAREN
        rparenToken = self.consume(TokenType.RIGHT_PAREN, "Expected ')'")
        node.addChild(ParseTreeNode("RIGHT_PAREN", token=rparenToken))
        
        return node
    
    def parseColumnList(self):
        """ColumnList → ColumnDef | ColumnDef COMMA ColumnList"""
        node = ParseTreeNode("ColumnList")
        
        # First column definition
        columnDef = self.parseColumnDef()
        node.addChild(columnDef)
        
        # More columns (comma-separated)
        while self.match(TokenType.COMMA):
            commaToken = self.consume(TokenType.COMMA)
            node.addChild(ParseTreeNode("COMMA", token=commaToken))
            columnDef = self.parseColumnDef()
            node.addChild(columnDef)
        
        return node
    
    def parseColumnDef(self):
        """ColumnDef → IDENTIFIER Type"""
        node = ParseTreeNode("ColumnDef")
        
        # IDENTIFIER (column name)
        idToken = self.consume(TokenType.IDENTIFIER, "Expected column name")
        node.addChild(ParseTreeNode("IDENTIFIER", token=idToken))
        
        # Type
        typeNode = self.parseType()
        node.addChild(typeNode)
        
        return node
    
    def parseType(self):
        """Type → INT | FLOAT | TEXT"""
        node = ParseTreeNode("Type")
        
        if self.match(TokenType.INT):
            token = self.consume(TokenType.INT, "Expected type (INT, FLOAT, or TEXT)")
        elif self.match(TokenType.FLOAT):
            token = self.consume(TokenType.FLOAT, "Expected type (INT, FLOAT, or TEXT)")
        elif self.match(TokenType.TEXT):
            token = self.consume(TokenType.TEXT, "Expected type (INT, FLOAT, or TEXT)")
        else:
            current = self.currentToken()
            raise ParserError(
                "Expected type (INT, FLOAT, or TEXT)",
                current.line if current else 0,
                current.col if current else 0,
                expected="INT, FLOAT, or TEXT",
                found=current.lexeme if current and current.lexeme else (current.tokenType if current else "EOF")
            )
        
        node.addChild(ParseTreeNode(token.tokenType, token=token))
        return node
    
    def parseInsertStatement(self):
        """InsertStmt → INSERT INTO IDENTIFIER VALUES LEFT_PAREN ValueList RIGHT_PAREN"""
        node = ParseTreeNode("InsertStmt")
        
        # INSERT
        insertToken = self.consume(TokenType.INSERT, "Expected 'INSERT'")
        node.addChild(ParseTreeNode("INSERT", token=insertToken))
        
        # INTO
        intoToken = self.consume(TokenType.INTO, "Expected 'INTO'")
        node.addChild(ParseTreeNode("INTO", token=intoToken))
        
        # IDENTIFIER (table name)
        idToken = self.consume(TokenType.IDENTIFIER, "Expected table name")
        node.addChild(ParseTreeNode("IDENTIFIER", token=idToken))
        
        # VALUES
        valuesToken = self.consume(TokenType.VALUES, "Expected 'VALUES'")
        node.addChild(ParseTreeNode("VALUES", token=valuesToken))
        
        # LEFT_PAREN
        lparenToken = self.consume(TokenType.LEFT_PAREN, "Expected '('")
        node.addChild(ParseTreeNode("LEFT_PAREN", token=lparenToken))
        
        # ValueList
        valueList = self.parseValueList()
        node.addChild(valueList)
        
        # RIGHT_PAREN
        rparenToken = self.consume(TokenType.RIGHT_PAREN, "Expected ')'")
        node.addChild(ParseTreeNode("RIGHT_PAREN", token=rparenToken))
        
        return node
    
    def parseValueList(self):
        """ValueList → Value | Value COMMA ValueList"""
        node = ParseTreeNode("ValueList")
        
        # First value
        valueNode = self.parseValue()
        node.addChild(valueNode)
        
        # More values (comma-separated)
        while self.match(TokenType.COMMA):
            commaToken = self.consume(TokenType.COMMA)
            node.addChild(ParseTreeNode("COMMA", token=commaToken))
            valueNode = self.parseValue()
            node.addChild(valueNode)
        
        return node
    
    def parseValue(self):
        """Value → NUMBER | STRING | IDENTIFIER"""
        node = ParseTreeNode("Value")
        
        if self.match(TokenType.NUMBER):
            token = self.consume(TokenType.NUMBER)
        elif self.match(TokenType.STRING):
            token = self.consume(TokenType.STRING)
        elif self.match(TokenType.IDENTIFIER):
            token = self.consume(TokenType.IDENTIFIER)
        else:
            current = self.currentToken()
            raise ParserError(
                "Expected value (NUMBER, STRING, or IDENTIFIER)",
                current.line if current else 0,
                current.col if current else 0,
                expected="NUMBER, STRING, or IDENTIFIER",
                found=current.lexeme if current and current.lexeme else (current.tokenType if current else "EOF")
            )
        
        node.addChild(ParseTreeNode(token.tokenType, token=token))
        return node
    
    def parseSelectStatement(self):
        """SelectStmt → SELECT SelectList FROM IDENTIFIER WhereClause"""
        node = ParseTreeNode("SelectStmt")
        
        # SELECT
        selectToken = self.consume(TokenType.SELECT, "Expected 'SELECT'")
        node.addChild(ParseTreeNode("SELECT", token=selectToken))
        
        # SelectList
        selectList = self.parseSelectList()
        node.addChild(selectList)
        
        # FROM
        fromToken = self.consume(TokenType.FROM, "Expected 'FROM'")
        node.addChild(ParseTreeNode("FROM", token=fromToken))
        
        # IDENTIFIER (table name)
        idToken = self.consume(TokenType.IDENTIFIER, "Expected table name")
        node.addChild(ParseTreeNode("IDENTIFIER", token=idToken))
        
        # WhereClause (optional)
        if self.match(TokenType.WHERE):
            whereClause = self.parseWhereClause()
            node.addChild(whereClause)
        
        return node
    
    def parseSelectList(self):
        """SelectList → '*' | ColumnNameList"""
        node = ParseTreeNode("SelectList")
        
        if self.match(TokenType.MULTIPLY):
            starToken = self.consume(TokenType.MULTIPLY)
            node.addChild(ParseTreeNode("MULTIPLY", token=starToken))
        else:
            columnNameList = self.parseColumnNameList()
            node.addChild(columnNameList)
        
        return node
    
    def parseColumnNameList(self):
        """ColumnNameList → ColumnName | ColumnName COMMA ColumnNameList"""
        node = ParseTreeNode("ColumnNameList")
        
        # First column name
        columnName = self.parseColumnName()
        node.addChild(columnName)
        
        # More column names (comma-separated)
        while self.match(TokenType.COMMA):
            commaToken = self.consume(TokenType.COMMA)
            node.addChild(ParseTreeNode("COMMA", token=commaToken))
            columnName = self.parseColumnName()
            node.addChild(columnName)
        
        return node
    
    def parseColumnName(self):
        """ColumnName → IDENTIFIER | Expression"""
        node = ParseTreeNode("ColumnName")
        
        # Check if it's an expression (starts with LEFT_PAREN)
        if self.match(TokenType.LEFT_PAREN):
            expr = self.parseExpression()
            node.addChild(expr)
        else:
            idToken = self.consume(TokenType.IDENTIFIER, "Expected column name or expression")
            node.addChild(ParseTreeNode("IDENTIFIER", token=idToken))
        
        return node
    
    def parseWhereClause(self):
        """WhereClause → WHERE Condition"""
        node = ParseTreeNode("WhereClause")
        
        # WHERE
        whereToken = self.consume(TokenType.WHERE, "Expected 'WHERE'")
        node.addChild(ParseTreeNode("WHERE", token=whereToken))
        
        # Condition
        condition = self.parseCondition()
        node.addChild(condition)
        
        return node
    
    def parseCondition(self):
        """Condition → SimpleCondition | Condition AND Condition | Condition OR Condition | NOT Condition | LEFT_PAREN Condition RIGHT_PAREN"""
        node = ParseTreeNode("Condition")
        
        # Handle NOT
        if self.match(TokenType.NOT):
            notToken = self.consume(TokenType.NOT)
            node.addChild(ParseTreeNode("NOT", token=notToken))
            condition = self.parseCondition()
            node.addChild(condition)
            return node
        
        # Handle parentheses
        if self.match(TokenType.LEFT_PAREN):
            lparenToken = self.consume(TokenType.LEFT_PAREN)
            node.addChild(ParseTreeNode("LEFT_PAREN", token=lparenToken))
            condition = self.parseCondition()
            node.addChild(condition)
            rparenToken = self.consume(TokenType.RIGHT_PAREN, "Expected ')'")
            node.addChild(ParseTreeNode("RIGHT_PAREN", token=rparenToken))
            
            # Check for AND/OR after parentheses
            if self.match(TokenType.AND) or self.match(TokenType.OR):
                return self.parseCompoundCondition(node)
            return node
        
        # Parse simple condition
        simpleCondition = self.parseSimpleCondition()
        node.addChild(simpleCondition)
        
        # Check for AND/OR
        if self.match(TokenType.AND) or self.match(TokenType.OR):
            return self.parseCompoundCondition(node)
        
        return node
    
    def parseCompoundCondition(self, leftCondition):
        """Parse compound condition with AND/OR"""
        node = ParseTreeNode("Condition")
        node.addChild(leftCondition)
        
        while self.match(TokenType.AND) or self.match(TokenType.OR):
            if self.match(TokenType.AND):
                andToken = self.consume(TokenType.AND)
                node.addChild(ParseTreeNode("AND", token=andToken))
            else:
                orToken = self.consume(TokenType.OR)
                node.addChild(ParseTreeNode("OR", token=orToken))
            
            # Parse right side
            rightCondition = self.parseCondition()
            node.addChild(rightCondition)
        
        return node
    
    def parseSimpleCondition(self):
        """SimpleCondition → Expression ComparisonOp Expression"""
        node = ParseTreeNode("SimpleCondition")
        
        # Left expression
        leftExpr = self.parseExpression()
        node.addChild(leftExpr)
        
        # Comparison operator
        compOp = self.parseComparisonOp()
        node.addChild(compOp)
        
        # Right expression
        rightExpr = self.parseExpression()
        node.addChild(rightExpr)
        
        return node
    
    def parseComparisonOp(self):
        """ComparisonOp → EQUAL | NOT_EQUAL | LESS_THAN | GREATER_THAN | LESS_EQUAL | GREATER_EQUAL"""
        node = ParseTreeNode("ComparisonOp")
        
        if self.match(TokenType.EQUAL):
            token = self.consume(TokenType.EQUAL)
        elif self.match(TokenType.NOT_EQUAL):
            token = self.consume(TokenType.NOT_EQUAL)
        elif self.match(TokenType.LESS_THAN):
            token = self.consume(TokenType.LESS_THAN)
        elif self.match(TokenType.GREATER_THAN):
            token = self.consume(TokenType.GREATER_THAN)
        elif self.match(TokenType.LESS_EQUAL):
            token = self.consume(TokenType.LESS_EQUAL)
        elif self.match(TokenType.GREATER_EQUAL):
            token = self.consume(TokenType.GREATER_EQUAL)
        else:
            current = self.currentToken()
            raise ParserError(
                "Expected comparison operator (=, !=, <, >, <=, >=)",
                current.line if current else 0,
                current.col if current else 0,
                expected="comparison operator",
                found=current.lexeme if current and current.lexeme else (current.tokenType if current else "EOF")
            )
        
        node.addChild(ParseTreeNode(token.tokenType, token=token))
        return node
    
    def parseExpression(self):
        """Expression → Term | Expression PLUS Term | Expression MINUS Term"""
        node = ParseTreeNode("Expression")
        
        # First term
        term = self.parseTerm()
        node.addChild(term)
        
        # More terms with +/- operators
        while self.match(TokenType.PLUS) or self.match(TokenType.MINUS):
            if self.match(TokenType.PLUS):
                plusToken = self.consume(TokenType.PLUS)
                node.addChild(ParseTreeNode("PLUS", token=plusToken))
            else:
                minusToken = self.consume(TokenType.MINUS)
                node.addChild(ParseTreeNode("MINUS", token=minusToken))
            
            term = self.parseTerm()
            node.addChild(term)
        
        return node
    
    def parseTerm(self):
        """Term → Factor | Term MULTIPLY Factor | Term DIVIDE Factor"""
        node = ParseTreeNode("Term")
        
        # First factor
        factor = self.parseFactor()
        node.addChild(factor)
        
        # More factors with */ operators
        while self.match(TokenType.MULTIPLY) or self.match(TokenType.DIVIDE):
            if self.match(TokenType.MULTIPLY):
                multToken = self.consume(TokenType.MULTIPLY)
                node.addChild(ParseTreeNode("MULTIPLY", token=multToken))
            else:
                divToken = self.consume(TokenType.DIVIDE)
                node.addChild(ParseTreeNode("DIVIDE", token=divToken))
            
            factor = self.parseFactor()
            node.addChild(factor)
        
        return node
    
    def parseFactor(self):
        """Factor → NUMBER | STRING | IDENTIFIER | LEFT_PAREN Expression RIGHT_PAREN"""
        node = ParseTreeNode("Factor")
        
        if self.match(TokenType.NUMBER):
            token = self.consume(TokenType.NUMBER)
            node.addChild(ParseTreeNode("NUMBER", token=token))
        elif self.match(TokenType.STRING):
            token = self.consume(TokenType.STRING)
            node.addChild(ParseTreeNode("STRING", token=token))
        elif self.match(TokenType.IDENTIFIER):
            token = self.consume(TokenType.IDENTIFIER)
            node.addChild(ParseTreeNode("IDENTIFIER", token=token))
        elif self.match(TokenType.LEFT_PAREN):
            lparenToken = self.consume(TokenType.LEFT_PAREN)
            node.addChild(ParseTreeNode("LEFT_PAREN", token=lparenToken))
            expr = self.parseExpression()
            node.addChild(expr)
            rparenToken = self.consume(TokenType.RIGHT_PAREN, "Expected ')'")
            node.addChild(ParseTreeNode("RIGHT_PAREN", token=rparenToken))
        else:
            current = self.currentToken()
            raise ParserError(
                "Expected factor (NUMBER, STRING, IDENTIFIER, or expression)",
                current.line if current else 0,
                current.col if current else 0,
                expected="NUMBER, STRING, IDENTIFIER, or '('",
                found=current.lexeme if current and current.lexeme else (current.tokenType if current else "EOF")
            )
        
        return node
    
    def parseUpdateStatement(self):
        """UpdateStmt → UPDATE IDENTIFIER SET AssignmentList WhereClause"""
        node = ParseTreeNode("UpdateStmt")
        
        # UPDATE
        updateToken = self.consume(TokenType.UPDATE, "Expected 'UPDATE'")
        node.addChild(ParseTreeNode("UPDATE", token=updateToken))
        
        # IDENTIFIER (table name)
        idToken = self.consume(TokenType.IDENTIFIER, "Expected table name")
        node.addChild(ParseTreeNode("IDENTIFIER", token=idToken))
        
        # SET
        setToken = self.consume(TokenType.SET, "Expected 'SET'")
        node.addChild(ParseTreeNode("SET", token=setToken))
        
        # AssignmentList
        assignmentList = self.parseAssignmentList()
        node.addChild(assignmentList)
        
        # WhereClause (optional)
        if self.match(TokenType.WHERE):
            whereClause = self.parseWhereClause()
            node.addChild(whereClause)
        
        return node
    
    def parseAssignmentList(self):
        """AssignmentList → Assignment | Assignment COMMA AssignmentList"""
        node = ParseTreeNode("AssignmentList")
        
        # First assignment
        assignment = self.parseAssignment()
        node.addChild(assignment)
        
        # More assignments (comma-separated)
        while self.match(TokenType.COMMA):
            commaToken = self.consume(TokenType.COMMA)
            node.addChild(ParseTreeNode("COMMA", token=commaToken))
            assignment = self.parseAssignment()
            node.addChild(assignment)
        
        return node
    
    def parseAssignment(self):
        """Assignment → IDENTIFIER EQUAL Expression"""
        node = ParseTreeNode("Assignment")
        
        # IDENTIFIER (column name)
        idToken = self.consume(TokenType.IDENTIFIER, "Expected column name")
        node.addChild(ParseTreeNode("IDENTIFIER", token=idToken))
        
        # EQUAL
        equalToken = self.consume(TokenType.EQUAL, "Expected '='")
        node.addChild(ParseTreeNode("EQUAL", token=equalToken))
        
        # Expression
        expr = self.parseExpression()
        node.addChild(expr)
        
        return node
    
    def parseDeleteStatement(self):
        """DeleteStmt → DELETE FROM IDENTIFIER WhereClause"""
        node = ParseTreeNode("DeleteStmt")
        
        # DELETE
        deleteToken = self.consume(TokenType.DELETE, "Expected 'DELETE'")
        node.addChild(ParseTreeNode("DELETE", token=deleteToken))
        
        # FROM
        fromToken = self.consume(TokenType.FROM, "Expected 'FROM'")
        node.addChild(ParseTreeNode("FROM", token=fromToken))
        
        # IDENTIFIER (table name)
        idToken = self.consume(TokenType.IDENTIFIER, "Expected table name")
        node.addChild(ParseTreeNode("IDENTIFIER", token=idToken))
        
        # WhereClause (optional)
        if self.match(TokenType.WHERE):
            whereClause = self.parseWhereClause()
            node.addChild(whereClause)
        
        return node
    
    def getErrors(self):
        """Get all collected parsing errors"""
        return self.errors


def main():
    """Main function to run the parser"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python parser.py <input_file>")
        sys.exit(1)
    
    inputFile = sys.argv[1]
    
    try:
        with open(inputFile, 'r') as f:
            source = f.read()
        
        # Tokenize
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        
        # Check for lexical errors
        lexErrors = lexer.getErrors()
        if lexErrors:
            print("Lexical Errors:")
            for error in lexErrors:
                print(f"  {error}")
            print()
        
        # Parse
        parser = Parser(tokens)
        parseTree = parser.parse()
        
        # Check for parsing errors
        parseErrors = parser.getErrors()
        if parseErrors:
            print("Syntax Errors:")
            for error in parseErrors:
                print(f"  {error}")
            print()
        
        # Print parse tree
        if not parseErrors:
            print("Parse Tree:")
            print(parseTree)
        else:
            print("Parse tree generation incomplete due to syntax errors.")
    
    except FileNotFoundError:
        print(f"Error: File '{inputFile}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
