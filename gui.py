#!/usr/bin/env python3
"""
Modern GUI for SQL Lexical Analyzer and Parser
Flask-based web interface with animations and beautiful design
"""

from flask import Flask, render_template, request, jsonify
from lexer import Lexer, LexerError
from parser import Parser, ParserError
import json
import os

# Configure Flask to use the gui folder for templates and static files
app = Flask(__name__, 
            template_folder='gui',
            static_folder='gui',
            static_url_path='/static')

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/tokenize', methods=['POST'])
def tokenize():
    """Handle tokenization requests"""
    try:
        data = request.get_json()
        sourceCode = data.get('code', '')
        
        if not sourceCode.strip():
            return jsonify({
                'success': False,
                'error': 'Please enter some code to tokenize'
            })
        
        try:
            lexer = Lexer(sourceCode)
            tokens = lexer.tokenize()
            
            # Check for errors
            errors = lexer.getErrors()
            if errors:
                # Return all errors
                errorList = []
                for error in errors:
                    errorList.append({
                        'message': error.message,
                        'line': error.line,
                        'col': error.col
                    })
                return jsonify({
                    'success': False,
                    'errors': errorList
                })

            # Detailed tokens list
            detailed = []
            for token in tokens:
                if token.tokenType != 'EOF':
                    detailed.append({
                        'type': token.tokenType,
                        'lexeme': token.lexeme,
                        'line': token.line,
                        'column': token.col
                    })

            mode = (data.get('mode') or 'detailed').lower()

            if mode == 'general':
                # Grouped analysis per assignment requirements
                groups = {
                    'Keywords': {'count': 0, 'examples': []},
                    'Identifiers': {'count': 0, 'examples': []},
                    'Literals': {'count': 0, 'examples': []},
                    'Operators': {'count': 0, 'examples': []},
                    'Delimiters': {'count': 0, 'examples': []},
                }

                keywords = {
                    'SELECT','FROM','WHERE','INSERT','INTO','VALUES','UPDATE','SET','DELETE','CREATE','TABLE','INT','FLOAT','TEXT','AND','OR','NOT'
                }
                literals = {'NUMBER','STRING'}
                operators = {
                    'EQUAL','NOT_EQUAL','LESS_THAN','GREATER_THAN','LESS_EQUAL','GREATER_EQUAL','PLUS','MINUS','MULTIPLY','DIVIDE'
                }
                delims = {'LEFT_PAREN','RIGHT_PAREN','COMMA','SEMICOLON'}

                total = 0
                for t in detailed:
                    tType = t['type']
                    total += 1
                    if tType in keywords:
                        g = groups['Keywords']
                    elif tType == 'IDENTIFIER':
                        g = groups['Identifiers']
                    elif tType in literals:
                        g = groups['Literals']
                    elif tType in operators:
                        g = groups['Operators']
                    elif tType in delims:
                        g = groups['Delimiters']
                    else:
                        # Unknowns count under Delimiters fallback
                        g = groups['Delimiters']
                    g['count'] += 1
                    if len(g['examples']) < 5:
                        g['examples'].append(t['lexeme'])

                return jsonify({
                    'success': True,
                    'mode': 'general',
                    'groups': groups,
                    'total': total,
                })
            else:
                return jsonify({
                    'success': True,
                    'mode': 'detailed',
                    'tokens': detailed,
                    'count': len(detailed)
                })
            
        except LexerError as e:
            # This should not happen now, but keep for backward compatibility
            return jsonify({
                'success': False,
                'errors': [{
                    'message': e.message,
                    'line': e.line,
                    'col': e.col
                }]
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
        })

@app.route('/parse', methods=['POST'])
def parse():
    """Handle parsing requests"""
    try:
        data = request.get_json()
        sourceCode = data.get('code', '')
        
        if not sourceCode.strip():
            return jsonify({
                'success': False,
                'error': 'Please enter some code to parse'
            })
        
        try:
            # First tokenize
            lexer = Lexer(sourceCode)
            tokens = lexer.tokenize()
            
            # Check for lexical errors
            lexErrors = lexer.getErrors()
            if lexErrors:
                errorList = []
                for error in lexErrors:
                    errorList.append({
                        'message': error.message,
                        'line': error.line,
                        'col': error.col,
                        'type': 'lexical'
                    })
                return jsonify({
                    'success': False,
                    'errors': errorList
                })
            
            # Then parse
            parser = Parser(tokens)
            parseTree = parser.parse()
            
            # Check for parsing errors
            parseErrors = parser.getErrors()
            if parseErrors:
                errorList = []
                for error in parseErrors:
                    errorList.append({
                        'message': error.message,
                        'line': error.line,
                        'col': error.col,
                        'type': 'syntax',
                        'expected': error.expected,
                        'found': error.found
                    })
                # Only include parse tree if there are few errors (partial success)
                parseTreeDict = None
                if len(parseErrors) <= 5 and parseTree:
                    try:
                        parseTreeDict = parseTree.toDict()
                    except:
                        pass  # Skip if serialization fails
                
                return jsonify({
                    'success': False,
                    'errors': errorList,
                    'parseTree': parseTreeDict
                })
            
            # Success - return parse tree
            try:
                parseTreeDict = parseTree.toDict()
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Failed to serialize parse tree: {str(e)}'
                })
            
            return jsonify({
                'success': True,
                'parseTree': parseTreeDict
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Parsing error: {str(e)}'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
        })

if __name__ == '__main__':
    print("🚀 Starting SQL Lexer & Parser GUI...")
    print("📝 Open your browser and navigate to: http://localhost:5001")
    print("✨ Enjoy the modern interface!")
    app.run(debug=True, host='0.0.0.0', port=5001)
