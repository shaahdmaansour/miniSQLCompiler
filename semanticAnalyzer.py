#!/usr/bin/env python3
"""
Semantic Analyzer for SQL-like language
Performs semantic checks on the parse tree from Phase 02
"""

from lexer import TokenType
from parser import ParseTreeNode


class SemanticError(Exception):
    """Custom exception for semantic errors"""
    def __init__(self, message, line, col):
        self.message = message
        self.line = line
        self.col = col
        super().__init__(f"Semantic Error: {message} at line {line}, position {col}.")


class ColumnInfo:
    """Represents information about a column"""
    def __init__(self, name, dataType):
        self.name = name
        self.dataType = dataType  # INT, FLOAT, or TEXT
    
    def __str__(self):
        return f"{self.name}: {self.dataType}"
    
    def toDict(self):
        return {
            'name': self.name,
            'type': self.dataType
        }


class TableInfo:
    """Represents information about a table and its columns"""
    def __init__(self, name):
        self.name = name
        self.columns = {}  # Dictionary mapping column name to ColumnInfo
    
    def addColumn(self, columnInfo):
        """Add a column to the table"""
        self.columns[columnInfo.name] = columnInfo
    
    def getColumn(self, columnName):
        """Get column information by name"""
        return self.columns.get(columnName)
    
    def hasColumn(self, columnName):
        """Check if table has a column"""
        return columnName in self.columns
    
    def toDict(self):
        return {
            'name': self.name,
            'columns': [col.toDict() for col in self.columns.values()]
        }


class SymbolTable:
    """Manages symbol table for tables and columns"""
    def __init__(self):
        self.tables = {}  # Dictionary mapping table name to TableInfo
    
    def addTable(self, tableInfo):
        """Add a table to the symbol table"""
        if tableInfo.name in self.tables:
            raise ValueError(f"Table '{tableInfo.name}' already exists")
        self.tables[tableInfo.name] = tableInfo
    
    def getTable(self, tableName):
        """Get table information by name"""
        return self.tables.get(tableName)
    
    def hasTable(self, tableName):
        """Check if table exists"""
        return tableName in self.tables
    
    def dump(self):
        """Dump symbol table contents"""
        result = {}
        for tableName, tableInfo in self.tables.items():
            result[tableName] = tableInfo.toDict()
        return result
    
    def __str__(self):
        lines = ["Symbol Table:"]
        for tableName, tableInfo in self.tables.items():
            lines.append(f"  Table: {tableName}")
            for colName, colInfo in tableInfo.columns.items():
                lines.append(f"    Column: {colInfo}")
        return "\n".join(lines)


class SemanticAnalyzer:
    """Semantic Analyzer for SQL-like language"""
    
    def __init__(self, parseTree):
        self.parseTree = parseTree
        self.symbolTable = SymbolTable()
        self.errors = []
        self.annotatedTree = None
    
    def analyze(self):
        """Perform semantic analysis on the parse tree"""
        try:
            # First pass: process CREATE TABLE statements to build symbol table
            self.buildSymbolTable()
            
            # Second pass: validate all statements
            self.validateStatements()
            
            # Third pass: annotate parse tree with semantic information
            self.annotatedTree = self.annotateTree(self.parseTree)
            
            return len(self.errors) == 0
        except Exception as e:
            self.errors.append(SemanticError(
                f"Unexpected error during semantic analysis: {str(e)}",
                0, 0
            ))
            return False
    
    def buildSymbolTable(self):
        """First pass: build symbol table from CREATE TABLE statements"""
        if not self.parseTree or self.parseTree.nodeType != "Query":
            return
        
        for child in self.parseTree.children:
            if child and child.nodeType == "CreateStmt":
                self.processCreateStatement(child)
    
    def processCreateStatement(self, node):
        """Process CREATE TABLE statement to add to symbol table"""
        # Structure: CREATE TABLE IDENTIFIER LEFT_PAREN ColumnList RIGHT_PAREN
        # Children: [CREATE, TABLE, IDENTIFIER, LEFT_PAREN, ColumnList, RIGHT_PAREN]
        tableNameNode = None
        columnListNode = None
        
        # Find table name (should be the IDENTIFIER at index 2, after CREATE and TABLE)
        if len(node.children) > 2:
            child = node.children[2]
            if child and child.nodeType == "IDENTIFIER" and child.token:
                tableNameNode = child
        
        # Find ColumnList (should be at index 4, after CREATE, TABLE, IDENTIFIER, LEFT_PAREN)
        for child in node.children:
            if child and child.nodeType == "ColumnList":
                columnListNode = child
                break
        
        if not tableNameNode or not tableNameNode.token:
            self.errors.append(SemanticError(
                "Missing table name in CREATE TABLE statement",
                0, 0
            ))
            return
        
        tableName = tableNameNode.token.lexeme
        
        # Check for redeclaration
        if self.symbolTable.hasTable(tableName):
            self.errors.append(SemanticError(
                f"Table '{tableName}' is already declared",
                tableNameNode.token.line,
                tableNameNode.token.col
            ))
            return
        
        # Create table info
        tableInfo = TableInfo(tableName)
        
        # Extract column definitions
        if columnListNode:
            self.extractColumns(columnListNode, tableInfo, tableNameNode.token.line)
        
        # Add table to symbol table
        try:
            self.symbolTable.addTable(tableInfo)
        except ValueError as e:
            # Should not happen due to check above, but handle just in case
            self.errors.append(SemanticError(
                str(e),
                tableNameNode.token.line,
                tableNameNode.token.col
            ))
    
    def extractColumns(self, columnListNode, tableInfo, defaultLine):
        """Extract column definitions from ColumnList node"""
        for child in columnListNode.children:
            if child and child.nodeType == "ColumnDef":
                columnName = None
                columnType = None
                
                # Extract column name and type
                for colChild in child.children:
                    if colChild and colChild.nodeType == "IDENTIFIER" and colChild.token:
                        columnName = colChild.token.lexeme
                    elif colChild and colChild.nodeType == "Type":
                        # Extract type from Type node
                        for typeChild in colChild.children:
                            if typeChild and typeChild.token:
                                typeTokenType = typeChild.token.tokenType
                                if typeTokenType in [TokenType.INT, TokenType.FLOAT, TokenType.TEXT]:
                                    columnType = typeTokenType
                                    break
                
                if columnName and columnType:
                    # Validate type
                    if columnType not in [TokenType.INT, TokenType.FLOAT, TokenType.TEXT]:
                        colToken = None
                        for colChild in child.children:
                            if colChild and colChild.nodeType == "IDENTIFIER" and colChild.token:
                                colToken = colChild.token
                                break
                        self.errors.append(SemanticError(
                            f"Invalid data type '{columnType}' for column '{columnName}'. Expected INT, FLOAT, or TEXT",
                            colToken.line if colToken else defaultLine,
                            colToken.col if colToken else 0
                        ))
                    else:
                        columnInfo = ColumnInfo(columnName, columnType)
                        tableInfo.addColumn(columnInfo)
                else:
                    # Missing column name or type
                    colToken = None
                    for colChild in child.children:
                        if colChild and colChild.nodeType == "IDENTIFIER" and colChild.token:
                            colToken = colChild.token
                            break
                    self.errors.append(SemanticError(
                        "Missing column name or type in column definition",
                        colToken.line if colToken else defaultLine,
                        colToken.col if colToken else 0
                    ))
    
    def validateStatements(self):
        """Second pass: validate all statements"""
        if not self.parseTree or self.parseTree.nodeType != "Query":
            return
        
        for child in self.parseTree.children:
            if not child:
                continue
            
            if child.nodeType == "CreateStmt":
                # Already processed in buildSymbolTable, but check for redeclaration again
                pass
            elif child.nodeType == "InsertStmt":
                self.validateInsertStatement(child)
            elif child.nodeType == "SelectStmt":
                self.validateSelectStatement(child)
            elif child.nodeType == "UpdateStmt":
                self.validateUpdateStatement(child)
            elif child.nodeType == "DeleteStmt":
                self.validateDeleteStatement(child)
    
    def validateInsertStatement(self, node):
        """Validate INSERT INTO statement"""
        # Structure: INSERT INTO IDENTIFIER VALUES LEFT_PAREN ValueList RIGHT_PAREN
        # Children: [INSERT, INTO, IDENTIFIER, VALUES, LEFT_PAREN, ValueList, RIGHT_PAREN]
        tableNameNode = None
        valueListNode = None
        
        # Find table name (should be the IDENTIFIER at index 2, after INSERT and INTO)
        if len(node.children) > 2:
            child = node.children[2]
            if child and child.nodeType == "IDENTIFIER" and child.token:
                tableNameNode = child
        
        # Find ValueList
        for child in node.children:
            if child and child.nodeType == "ValueList":
                valueListNode = child
                break
        
        if not tableNameNode or not tableNameNode.token:
            return
        
        tableName = tableNameNode.token.lexeme
        
        # Check table existence
        if not self.symbolTable.hasTable(tableName):
            self.errors.append(SemanticError(
                f"Table '{tableName}' does not exist",
                tableNameNode.token.line,
                tableNameNode.token.col
            ))
            return
        
        tableInfo = self.symbolTable.getTable(tableName)
        
        # Extract values
        values = []
        if valueListNode:
            values = self.extractValues(valueListNode)
        
        # Check number of values matches number of columns
        expectedCount = len(tableInfo.columns)
        actualCount = len(values)
        
        if actualCount != expectedCount:
            valueToken = None
            if valueListNode and valueListNode.children:
                for child in valueListNode.children:
                    if child and child.token:
                        valueToken = child.token
                        break
            self.errors.append(SemanticError(
                f"Number of values ({actualCount}) does not match number of columns ({expectedCount}) for table '{tableName}'",
                valueToken.line if valueToken else tableNameNode.token.line,
                valueToken.col if valueToken else tableNameNode.token.col
            ))
            return
        
        # Check type consistency
        columnList = list(tableInfo.columns.values())
        for i, value in enumerate(values):
            if i < len(columnList):
                columnInfo = columnList[i]
                valueType = self.getLiteralType(value)
                
                if not self.isTypeCompatible(columnInfo.dataType, valueType):
                    valueToken = value.get('token') if isinstance(value, dict) else None
                    self.errors.append(SemanticError(
                        f"Type mismatch: Column '{columnInfo.name}' is defined as {columnInfo.dataType}, but a {valueType} literal was provided for insertion",
                        valueToken['line'] if valueToken and isinstance(valueToken, dict) else (valueToken.line if valueToken else tableNameNode.token.line),
                        valueToken['col'] if valueToken and isinstance(valueToken, dict) else (valueToken.col if valueToken else tableNameNode.token.col)
                    ))
    
    def extractValues(self, valueListNode):
        """Extract values from ValueList node"""
        values = []
        for child in valueListNode.children:
            if child and child.nodeType == "Value":
                # Extract the actual value token
                for valueChild in child.children:
                    if valueChild and valueChild.token:
                        tokenType = valueChild.token.tokenType
                        if tokenType in [TokenType.NUMBER, TokenType.STRING, TokenType.IDENTIFIER]:
                            values.append({
                                'type': tokenType,
                                'lexeme': valueChild.token.lexeme,
                                'token': valueChild.token
                            })
                            break
            # Skip COMMA nodes
        return values
    
    def getLiteralType(self, value):
        """Get the data type of a literal value"""
        if isinstance(value, dict):
            tokenType = value.get('type')
            if tokenType == TokenType.NUMBER:
                # Check if it's INT or FLOAT
                lexeme = value.get('lexeme', '')
                if '.' in lexeme:
                    return TokenType.FLOAT
                else:
                    return TokenType.INT
            elif tokenType == TokenType.STRING:
                return TokenType.TEXT
        return None
    
    def isTypeCompatible(self, expectedType, actualType):
        """Check if actual type is compatible with expected type"""
        if expectedType == TokenType.INT:
            return actualType == TokenType.INT
        elif expectedType == TokenType.FLOAT:
            return actualType in [TokenType.INT, TokenType.FLOAT]  # INT can be promoted to FLOAT
        elif expectedType == TokenType.TEXT:
            return actualType == TokenType.TEXT
        return False
    
    def validateSelectStatement(self, node):
        """Validate SELECT statement"""
        # Structure: SELECT SelectList FROM IDENTIFIER WhereClause
        # Children: [SELECT, SelectList, FROM, IDENTIFIER, WhereClause?]
        tableNameNode = None
        selectListNode = None
        whereClauseNode = None
        
        # Find SelectList (should be at index 1, after SELECT)
        if len(node.children) > 1:
            child = node.children[1]
            if child and child.nodeType == "SelectList":
                selectListNode = child
        
        # Find table name (should be the IDENTIFIER after FROM)
        for i, child in enumerate(node.children):
            if child and child.nodeType == "FROM":
                # Next child should be IDENTIFIER (table name)
                if i + 1 < len(node.children):
                    nextChild = node.children[i + 1]
                    if nextChild and nextChild.nodeType == "IDENTIFIER" and nextChild.token:
                        tableNameNode = nextChild
                break
        
        # Find WhereClause (optional)
        for child in node.children:
            if child and child.nodeType == "WhereClause":
                whereClauseNode = child
                break
        
        if not tableNameNode or not tableNameNode.token:
            return
        
        tableName = tableNameNode.token.lexeme
        
        # Check table existence
        if not self.symbolTable.hasTable(tableName):
            self.errors.append(SemanticError(
                f"Table '{tableName}' does not exist",
                tableNameNode.token.line,
                tableNameNode.token.col
            ))
            return
        
        tableInfo = self.symbolTable.getTable(tableName)
        
        # Validate column names in SELECT list (if not *)
        if selectListNode:
            isStar = False
            for child in selectListNode.children:
                if child and child.nodeType == "MULTIPLY":
                    isStar = True
                    break
            
            if not isStar:
                # Validate column names
                columnNameList = None
                for child in selectListNode.children:
                    if child and child.nodeType == "ColumnNameList":
                        columnNameList = child
                        break
                
                if columnNameList:
                    self.validateColumnNames(columnNameList, tableInfo, tableName)
        
        # Validate WHERE clause
        if whereClauseNode:
            self.validateWhereClause(whereClauseNode, tableInfo, tableName)
    
    def validateUpdateStatement(self, node):
        """Validate UPDATE statement"""
        # Structure: UPDATE IDENTIFIER SET AssignmentList WhereClause
        # Children: [UPDATE, IDENTIFIER, SET, AssignmentList, WhereClause?]
        tableNameNode = None
        assignmentListNode = None
        whereClauseNode = None
        
        # Find table name (should be the IDENTIFIER at index 1, after UPDATE)
        if len(node.children) > 1:
            child = node.children[1]
            if child and child.nodeType == "IDENTIFIER" and child.token:
                tableNameNode = child
        
        # Find AssignmentList (should be after SET)
        for i, child in enumerate(node.children):
            if child and child.nodeType == "SET":
                # Next child should be AssignmentList
                if i + 1 < len(node.children):
                    nextChild = node.children[i + 1]
                    if nextChild and nextChild.nodeType == "AssignmentList":
                        assignmentListNode = nextChild
                break
        
        # Find WhereClause (optional)
        for child in node.children:
            if child and child.nodeType == "WhereClause":
                whereClauseNode = child
                break
        
        if not tableNameNode or not tableNameNode.token:
            return
        
        tableName = tableNameNode.token.lexeme
        
        # Check table existence
        if not self.symbolTable.hasTable(tableName):
            self.errors.append(SemanticError(
                f"Table '{tableName}' does not exist",
                tableNameNode.token.line,
                tableNameNode.token.col
            ))
            return
        
        tableInfo = self.symbolTable.getTable(tableName)
        
        # Validate column names in assignments
        if assignmentListNode:
            for child in assignmentListNode.children:
                if child and child.nodeType == "Assignment":
                    # Find column name
                    for assignChild in child.children:
                        if assignChild and assignChild.nodeType == "IDENTIFIER" and assignChild.token:
                            columnName = assignChild.token.lexeme
                            if not tableInfo.hasColumn(columnName):
                                self.errors.append(SemanticError(
                                    f"Column '{columnName}' does not exist in table '{tableName}'",
                                    assignChild.token.line,
                                    assignChild.token.col
                                ))
                            break
        
        # Validate WHERE clause
        if whereClauseNode:
            self.validateWhereClause(whereClauseNode, tableInfo, tableName)
    
    def validateDeleteStatement(self, node):
        """Validate DELETE statement"""
        # Structure: DELETE FROM IDENTIFIER WhereClause
        # Children: [DELETE, FROM, IDENTIFIER, WhereClause?]
        tableNameNode = None
        whereClauseNode = None
        
        # Find table name (should be the IDENTIFIER at index 2, after DELETE and FROM)
        if len(node.children) > 2:
            child = node.children[2]
            if child and child.nodeType == "IDENTIFIER" and child.token:
                tableNameNode = child
        
        # Find WhereClause (optional)
        for child in node.children:
            if child and child.nodeType == "WhereClause":
                whereClauseNode = child
                break
        
        if not tableNameNode or not tableNameNode.token:
            return
        
        tableName = tableNameNode.token.lexeme
        
        # Check table existence
        if not self.symbolTable.hasTable(tableName):
            self.errors.append(SemanticError(
                f"Table '{tableName}' does not exist",
                tableNameNode.token.line,
                tableNameNode.token.col
            ))
            return
        
        tableInfo = self.symbolTable.getTable(tableName)
        
        # Validate WHERE clause
        if whereClauseNode:
            self.validateWhereClause(whereClauseNode, tableInfo, tableName)
    
    def validateColumnNames(self, columnNameListNode, tableInfo, tableName):
        """Validate column names in a column name list"""
        # Track tables involved in this query (for ambiguity checking)
        involvedTables = [tableName]
        
        for child in columnNameListNode.children:
            if child and child.nodeType == "ColumnName":
                # Extract identifier from ColumnName
                for colChild in child.children:
                    if colChild and colChild.nodeType == "IDENTIFIER" and colChild.token:
                        columnName = colChild.token.lexeme
                        if not tableInfo.hasColumn(columnName):
                            self.errors.append(SemanticError(
                                f"Column '{columnName}' does not exist in table '{tableName}'",
                                colChild.token.line,
                                colChild.token.col
                            ))
                        else:
                            # Check for ambiguity across multiple tables
                            self.checkColumnAmbiguity(columnName, involvedTables, colChild.token)
                        break
    
    def validateWhereClause(self, whereClauseNode, tableInfo, tableName):
        """Validate WHERE clause"""
        # Find Condition node
        conditionNode = None
        for child in whereClauseNode.children:
            if child and child.nodeType == "Condition":
                conditionNode = child
                break
        
        if conditionNode:
            # Track tables involved for ambiguity checking
            involvedTables = [tableName]
            self.validateCondition(conditionNode, tableInfo, tableName, involvedTables)
    
    def validateCondition(self, conditionNode, tableInfo, tableName, involvedTables=None):
        """Validate condition recursively"""
        if involvedTables is None:
            involvedTables = [tableName]
        
        # Check for SimpleCondition
        for child in conditionNode.children:
            if child and child.nodeType == "SimpleCondition":
                self.validateSimpleCondition(child, tableInfo, tableName, involvedTables)
            elif child and child.nodeType == "Condition":
                # Recursive validation
                self.validateCondition(child, tableInfo, tableName, involvedTables)
    
    def validateSimpleCondition(self, simpleConditionNode, tableInfo, tableName, involvedTables=None):
        """Validate simple condition (expression comparison expression)"""
        if involvedTables is None:
            involvedTables = [tableName]
        
        expressions = []
        comparisonOp = None
        
        for child in simpleConditionNode.children:
            if child and child.nodeType == "Expression":
                expressions.append(child)
            elif child and child.nodeType == "ComparisonOp":
                comparisonOp = child
        
        if len(expressions) == 2:
            leftExpr = expressions[0]
            rightExpr = expressions[1]
            
            # Check for ambiguous column names in expressions
            self.checkExpressionForAmbiguity(leftExpr, involvedTables)
            self.checkExpressionForAmbiguity(rightExpr, involvedTables)
            
            # Check type compatibility
            leftType = self.getExpressionType(leftExpr, tableInfo, tableName)
            rightType = self.getExpressionType(rightExpr, tableInfo, tableName)
            
            if leftType and rightType and not self.isTypeCompatibleForComparison(leftType, rightType):
                # Find token for error reporting (prefer right expression, fallback to left)
                errorToken = None
                # Try right expression first
                errorToken = self.getFirstTokenFromExpression(rightExpr)
                if not errorToken:
                    # Fallback to left expression
                    errorToken = self.getFirstTokenFromExpression(leftExpr)
                # Fallback to comparison operator
                if not errorToken and comparisonOp:
                    for child in comparisonOp.children:
                        if child and child.token:
                            errorToken = child.token
                            break
                
                self.errors.append(SemanticError(
                    f"Type mismatch in comparison: Cannot compare {leftType} with {rightType}",
                    errorToken.line if errorToken else 0,
                    errorToken.col if errorToken else 0
                ))
    
    def checkColumnAmbiguity(self, columnName, involvedTables, token):
        """
        Check if a column name is ambiguous across multiple tables.
        
        This method checks if a column name exists in multiple tables that are
        involved in the current query. If so, it reports an ambiguity error.
        
        Note: The current grammar only supports single-table queries, so this
        check will typically not trigger errors. However, the infrastructure
        is in place and will work correctly if the grammar is extended to
        support JOINs or multiple tables in the FROM clause.
        
        Args:
            columnName: The name of the column to check
            involvedTables: List of table names involved in the current query
            token: The token representing the column name (for error reporting)
        """
        if len(involvedTables) <= 1:
            # Only one table involved, no ambiguity possible
            return
        
        # Find all tables that have this column
        tablesWithColumn = []
        for tableName in involvedTables:
            tableInfo = self.symbolTable.getTable(tableName)
            if tableInfo and tableInfo.hasColumn(columnName):
                tablesWithColumn.append(tableName)
        
        # If column exists in multiple tables, it's ambiguous
        if len(tablesWithColumn) > 1:
            self.errors.append(SemanticError(
                f"Column '{columnName}' is ambiguous: it exists in multiple tables ({', '.join(tablesWithColumn)}). Use table.column format to disambiguate.",
                token.line,
                token.col
            ))
    
    def checkExpressionForAmbiguity(self, exprNode, involvedTables):
        """Check an expression for ambiguous column references"""
        if not exprNode or len(involvedTables) <= 1:
            return
        
        # Recursively search for identifier tokens (column names)
        for child in exprNode.children:
            if child and child.nodeType == "Term":
                for termChild in child.children:
                    if termChild and termChild.nodeType == "Factor":
                        for factorChild in termChild.children:
                            if factorChild and factorChild.token:
                                tokenType = factorChild.token.tokenType
                                if tokenType == TokenType.IDENTIFIER:
                                    # Check if this identifier is a column name
                                    columnName = factorChild.token.lexeme
                                    self.checkColumnAmbiguity(columnName, involvedTables, factorChild.token)
    
    def getFirstTokenFromExpression(self, exprNode):
        """Get the first token from an expression node"""
        if not exprNode:
            return None
        
        # Recursively search for first token
        for child in exprNode.children:
            if child and child.token:
                return child.token
            # Recursively search in child
            token = self.getFirstTokenFromExpression(child)
            if token:
                return token
        return None
    
    def getExpressionType(self, exprNode, tableInfo, tableName):
        """Get the data type of an expression"""
        # For now, handle simple cases: NUMBER, STRING, IDENTIFIER
        for child in exprNode.children:
            if child and child.nodeType == "Term":
                for termChild in child.children:
                    if termChild and termChild.nodeType == "Factor":
                        for factorChild in termChild.children:
                            if factorChild and factorChild.token:
                                tokenType = factorChild.token.tokenType
                                if tokenType == TokenType.NUMBER:
                                    # Check if INT or FLOAT
                                    lexeme = factorChild.token.lexeme
                                    if '.' in lexeme:
                                        return TokenType.FLOAT
                                    else:
                                        return TokenType.INT
                                elif tokenType == TokenType.STRING:
                                    return TokenType.TEXT
                                elif tokenType == TokenType.IDENTIFIER:
                                    # Look up column type
                                    columnName = factorChild.token.lexeme
                                    columnInfo = tableInfo.getColumn(columnName)
                                    if columnInfo:
                                        return columnInfo.dataType
                                    else:
                                        # Column doesn't exist - error already reported
                                        return None
        return None
    
    def isTypeCompatibleForComparison(self, leftType, rightType):
        """Check if two types are compatible for comparison"""
        # Numeric types can be compared
        if leftType in [TokenType.INT, TokenType.FLOAT] and rightType in [TokenType.INT, TokenType.FLOAT]:
            return True
        # Same types are compatible
        if leftType == rightType:
            return True
        return False
    
    def annotateTree(self, node, context=None):
        """Annotate parse tree with semantic information"""
        if not node:
            return None
        
        # Create annotated node
        annotated = {
            'nodeType': node.nodeType,
            'children': [],
            'semanticInfo': {}
        }
        
        # Update context based on node type
        newContext = context
        if node.nodeType == "CreateStmt":
            # Extract table name for context
            if len(node.children) > 2:
                tableNameNode = node.children[2]
                if tableNameNode and tableNameNode.nodeType == "IDENTIFIER" and tableNameNode.token:
                    newContext = {'table': tableNameNode.token.lexeme}
        elif node.nodeType in ["SelectStmt", "UpdateStmt", "DeleteStmt", "InsertStmt"]:
            # Extract table name for context
            tableName = self.getTableNameFromStatement(node)
            if tableName:
                newContext = {'table': tableName}
        
        # Add token information
        if node.token:
            annotated['token'] = {
                'type': node.token.tokenType,
                'lexeme': node.token.lexeme,
                'line': node.token.line,
                'col': node.token.col
            }
            
            # Annotate with data type for literals and identifiers
            if node.token.tokenType == TokenType.NUMBER:
                if '.' in node.token.lexeme:
                    annotated['semanticInfo']['dataType'] = TokenType.FLOAT
                else:
                    annotated['semanticInfo']['dataType'] = TokenType.INT
            elif node.token.tokenType == TokenType.STRING:
                annotated['semanticInfo']['dataType'] = TokenType.TEXT
            elif node.token.tokenType == TokenType.IDENTIFIER:
                # Try to find column info using context
                identifierName = node.token.lexeme
                if newContext and 'table' in newContext:
                    tableInfo = self.symbolTable.getTable(newContext['table'])
                    if tableInfo:
                        columnInfo = tableInfo.getColumn(identifierName)
                        if columnInfo:
                            annotated['semanticInfo']['dataType'] = columnInfo.dataType
                            annotated['semanticInfo']['symbolTableRef'] = {
                                'table': tableInfo.name,
                                'column': columnInfo.name
                            }
                else:
                    # Try all tables (for ambiguous cases)
                    for tableInfo in self.symbolTable.tables.values():
                        columnInfo = tableInfo.getColumn(identifierName)
                        if columnInfo:
                            annotated['semanticInfo']['dataType'] = columnInfo.dataType
                            annotated['semanticInfo']['symbolTableRef'] = {
                                'table': tableInfo.name,
                                'column': columnInfo.name
                            }
                            break
        
        # Recursively annotate children with context
        for child in node.children:
            annotatedChild = self.annotateTree(child, newContext)
            if annotatedChild:
                annotated['children'].append(annotatedChild)
        
        return annotated
    
    def getTableNameFromStatement(self, node):
        """Extract table name from a statement node"""
        if node.nodeType == "SelectStmt":
            # Find IDENTIFIER after FROM
            for i, child in enumerate(node.children):
                if child and child.nodeType == "FROM":
                    if i + 1 < len(node.children):
                        nextChild = node.children[i + 1]
                        if nextChild and nextChild.nodeType == "IDENTIFIER" and nextChild.token:
                            return nextChild.token.lexeme
        elif node.nodeType == "UpdateStmt":
            # IDENTIFIER at index 1
            if len(node.children) > 1:
                child = node.children[1]
                if child and child.nodeType == "IDENTIFIER" and child.token:
                    return child.token.lexeme
        elif node.nodeType == "DeleteStmt":
            # IDENTIFIER at index 2
            if len(node.children) > 2:
                child = node.children[2]
                if child and child.nodeType == "IDENTIFIER" and child.token:
                    return child.token.lexeme
        elif node.nodeType == "InsertStmt":
            # IDENTIFIER at index 2
            if len(node.children) > 2:
                child = node.children[2]
                if child and child.nodeType == "IDENTIFIER" and child.token:
                    return child.token.lexeme
        return None
    
    def getErrors(self):
        """Get all semantic errors"""
        return self.errors
    
    def getSymbolTable(self):
        """Get symbol table"""
        return self.symbolTable
    
    def getAnnotatedTree(self):
        """Get annotated parse tree"""
        return self.annotatedTree

