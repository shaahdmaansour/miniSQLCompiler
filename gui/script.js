// Modern SQL Lexer GUI - Interactive JavaScript

document.addEventListener('DOMContentLoaded', () => {
    const codeInput = document.getElementById('codeInput');
    const tokenizeBtn = document.getElementById('tokenizeBtn');
    const clearBtn = document.getElementById('clearBtn');
    const fileUpload = document.getElementById('fileUpload');
    const downloadTxtBtn = document.getElementById('downloadTxtBtn');
    const downloadPdfBtn = document.getElementById('downloadPdfBtn');
    const resultsPanel = document.getElementById('resultsPanel');
    const resultsContainer = document.getElementById('resultsContainer');
    const errorContainer = document.getElementById('errorContainer');
    const errorsList = document.getElementById('errorsList');
    const noResults = document.getElementById('noResults');
    const tokenCount = document.getElementById('tokenCount');
    
    // Store current tokens for download
    let currentTokens = [];
    let currentFileName = 'tokens';

    // Helper: truncate text to fit a given width in the current doc/font
    function truncateToWidth(text, maxWidth, doc) {
        if (!text) return '';
        const ellipsis = '…';
        let t = String(text);
        if (doc.getTextWidth(t) <= maxWidth) return t;
        while (t.length > 0 && doc.getTextWidth(t + ellipsis) > maxWidth) {
            t = t.slice(0, -1);
        }
        return t + ellipsis;
    }

    // Helper: compute output base file name as "[uploadedName]Tokens"
    function getOutputBaseName() {
        const base = (currentFileName && currentFileName.trim().length > 0)
            ? currentFileName.trim()
            : 'Input';
        return `${base}Tokens`;
    }

    // Keyboard shortcuts
    codeInput.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            tokenizeCode();
        }
    });

    // Tokenize button event
    tokenizeBtn.addEventListener('click', tokenizeCode);

    // Clear button event
    clearBtn.addEventListener('click', () => {
        codeInput.value = '';
        codeInput.focus();
    });

    // File upload event
    fileUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            currentFileName = file.name.replace(/\.[^/.]+$/, ''); // Remove extension
            const reader = new FileReader();
            reader.onload = (event) => {
                codeInput.value = event.target.result;
                // Auto tokenize after upload
                tokenizeCode();
            };
            reader.readAsText(file);
        }
    });
    
    // Download button events
    downloadTxtBtn.addEventListener('click', downloadAsTxt);
    downloadPdfBtn.addEventListener('click', downloadAsPdf);

    // Tokenize function
    async function tokenizeCode() {
        const code = codeInput.value.trim();
        const analysisMode = document.getElementById('analysisMode')?.value || 'detailed';
        
        if (!code) {
            showError('Please enter some code to tokenize');
            return;
        }

        // Show loading state
        setLoading(true);
        hideResults();
        
        try {
            const response = await fetch('/tokenize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ code, mode: analysisMode })
            });

            const data = await response.json();
            
            if (data.success) {
                // Detailed mode
                if (analysisMode === 'detailed') {
                    currentTokens = data.tokens || [];
                    showTokens(currentTokens);
                    tokenCount.textContent = `${data.count || currentTokens.length} tokens`;
                    downloadTxtBtn.classList.remove('hidden');
                    downloadPdfBtn.classList.remove('hidden');
                } else {
                    // General mode
                    currentTokens = data.tokens || [];
                    showGeneralSummary(data.groups || {}, data.total || 0);
                    tokenCount.textContent = `${data.total || 0} tokens (general)`;
                    // Hide detailed download for general summary
                    downloadTxtBtn.classList.add('hidden');
                    downloadPdfBtn.classList.add('hidden');
                }
            } else {
                // Handle multiple errors
                if (data.errors && Array.isArray(data.errors)) {
                    showErrors(data.errors);
                } else if (data.error) {
                    // Backward compatibility: single error
                    showErrors([{
                        message: data.error.message || data.error,
                        line: data.error.line,
                        col: data.error.col
                    }]);
                } else {
                    showError('An unknown error occurred');
                }
            }
        } catch (error) {
            showError('An error occurred while tokenizing. Please try again.');
            console.error('Error:', error);
        } finally {
            setLoading(false);
        }
    }

    // Show tokens
    function showTokens(tokens) {
        resultsContainer.innerHTML = '';
        noResults.classList.add('hidden');
        errorContainer.classList.add('hidden');
        resultsContainer.classList.remove('hidden');
        
        // Delay animation for each token
        tokens.forEach((token, index) => {
            setTimeout(() => {
                const card = createTokenCard(token);
                resultsContainer.appendChild(card);
            }, index * 20); // Stagger animation
        });
    }

    // Show general grouped summary
    function showGeneralSummary(groups, total) {
        resultsContainer.innerHTML = '';
        noResults.classList.add('hidden');
        errorContainer.classList.add('hidden');
        resultsContainer.classList.remove('hidden');

        const order = ['Keywords', 'Identifiers', 'Literals', 'Operators', 'Delimiters'];
        order.forEach((key) => {
            const group = groups[key];
            if (!group) return;

            const card = document.createElement('div');
            card.className = 'token-card';
            card.innerHTML = `
                <div class="token-type token-identifier">${key}</div>
                <div class="token-lexeme">Count: ${group.count || 0}</div>
                ${group.examples && group.examples.length ? `<div class="token-position">Examples: ${group.examples.slice(0,5).join(', ')}</div>` : ''}
            `;
            resultsContainer.appendChild(card);
        });
    }

    // Create token card element
    function createTokenCard(token) {
        const card = document.createElement('div');
        card.className = 'token-card';
        
        const typeClass = getTokenTypeClass(token.type);
        const formattedLexeme = formatLexeme(token.lexeme);
        
        card.innerHTML = `
            <div class="token-type token-${typeClass}">${token.type}</div>
            <div class="token-lexeme">${formattedLexeme}</div>
            <div class="token-position">Line ${token.line}, Col ${token.column}</div>
        `;
        
        // Add click animation
        card.addEventListener('click', () => {
            card.style.transform = 'scale(0.95)';
            setTimeout(() => {
                card.style.transform = '';
            }, 150);
        });
        
        return card;
    }

    // Get CSS class for token type
    function getTokenTypeClass(tokenType) {
        const typeMap = {
            'SELECT': 'keyword',
            'FROM': 'keyword',
            'WHERE': 'keyword',
            'INSERT': 'keyword',
            'INTO': 'keyword',
            'VALUES': 'keyword',
            'UPDATE': 'keyword',
            'SET': 'keyword',
            'DELETE': 'keyword',
            'CREATE': 'keyword',
            'TABLE': 'keyword',
            'INT': 'keyword',
            'FLOAT': 'keyword',
            'TEXT': 'keyword',
            'AND': 'keyword',
            'OR': 'keyword',
            'NOT': 'keyword',
            'IDENTIFIER': 'identifier',
            'NUMBER': 'literal',
            'STRING': 'literal',
            'EQUAL': 'operator',
            'NOT_EQUAL': 'operator',
            'LESS_THAN': 'operator',
            'GREATER_THAN': 'operator',
            'LESS_EQUAL': 'operator',
            'GREATER_EQUAL': 'operator',
            'PLUS': 'operator',
            'MINUS': 'operator',
            'MULTIPLY': 'operator',
            'DIVIDE': 'operator',
            'LEFT_PAREN': 'punctuation',
            'RIGHT_PAREN': 'punctuation',
            'COMMA': 'punctuation',
            'SEMICOLON': 'punctuation',
        };
        
        return typeMap[tokenType] || 'identifier';
    }

    // Format lexeme for display
    function formatLexeme(lexeme) {
        // Escape HTML characters
        let formatted = lexeme
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
        
        // Add highlighting for strings
        if (lexeme.startsWith("'") && lexeme.endsWith("'")) {
            return `<span style="color: var(--token-literal);">${formatted}</span>`;
        }
        
        return formatted;
    }

    // Show single error (backward compatibility)
    function showError(message, line, col) {
        showErrors([{
            message: message,
            line: line,
            col: col
        }]);
    }
    
    // Show multiple errors
    function showErrors(errors) {
        noResults.classList.add('hidden');
        resultsContainer.classList.add('hidden');
        errorContainer.classList.remove('hidden');
        downloadTxtBtn.classList.add('hidden');
        downloadPdfBtn.classList.add('hidden');
        currentTokens = []; // Clear tokens on error
        
        errorsList.innerHTML = '';
        
        if (errors.length === 0) {
            errorsList.innerHTML = '<div class="error-box"><div class="error-icon">⚠️</div><div class="error-content"><h3>Error</h3><p>Unknown error occurred</p></div></div>';
            return;
        }
        
        // Display all errors
        errors.forEach((error, index) => {
            const errorBox = document.createElement('div');
            errorBox.className = 'error-box';
            errorBox.style.animationDelay = `${index * 0.1}s`; // Stagger animation
            
            const message = error.message || 'Unknown error';
            const line = error.line;
            const col = error.col;
            
            errorBox.innerHTML = `
                <div class="error-icon">⚠️</div>
                <div class="error-content">
                    <h3>Lexical Error ${errors.length > 1 ? `#${index + 1}` : ''}</h3>
                    <p>${escapeHtml(message)}</p>
                    ${line && col ? `<div class="error-position">Line ${line}, Column ${col}</div>` : ''}
                </div>
            `;
            
            errorsList.appendChild(errorBox);
        });
    }
    
    // Helper function to escape HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Hide all results
    function hideResults() {
        noResults.classList.add('hidden');
        resultsContainer.classList.add('hidden');
        errorContainer.classList.add('hidden');
    }

    // Set loading state
    function setLoading(loading) {
        if (loading) {
            tokenizeBtn.classList.add('loading');
            tokenizeBtn.disabled = true;
        } else {
            tokenizeBtn.classList.remove('loading');
            tokenizeBtn.disabled = false;
        }
    }
    
    // Download results as TXT
    function downloadAsTxt() {
        if (currentTokens.length === 0) return;
        
        // Clean, simple format
        const textData = currentTokens.map((token, idx) => 
            `${idx + 1}. ${token.type.padEnd(20)} | ${token.lexeme.padEnd(25)} | Line ${token.line}, Col ${token.column}`
        ).join('\n');
        
        // Create download link
        const blob = new Blob([textData], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${getOutputBaseName()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        // Animate button
        downloadTxtBtn.style.transform = 'scale(0.95)';
        setTimeout(() => downloadTxtBtn.style.transform = '', 150);
    }
    
    // Download results as PDF
    function downloadAsPdf() {
        if (currentTokens.length === 0) return;
        
        // Ensure jsPDF is available
        if (!window.jspdf || !window.jspdf.jsPDF) {
            console.error('jsPDF not loaded. Ensure the CDN script is accessible.');
            alert('PDF generator not loaded. Please check your internet connection and hard refresh (Cmd/Ctrl+Shift+R).');
            return;
        }
        
        const { jsPDF } = window.jspdf;
        let doc;
        try {
            doc = new jsPDF();
        } catch (e) {
            console.error('Failed to initialize jsPDF:', e);
            alert('Failed to initialize PDF. Please try TXT download instead.');
            return;
        }
        
        // Header
        doc.setFontSize(18);
        doc.setFont('helvetica', 'bold');
        doc.text('Token Analysis', 105, 20, { align: 'center' });
        
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.text(`File: ${currentFileName}`, 105, 30, { align: 'center' });
        doc.text(`Total Tokens: ${currentTokens.length}`, 105, 36, { align: 'center' });
        
        // Table headers (Lexeme, Token, Position) with wider spacing
        // Layout constants for equal column spacing
        const PAGE_WIDTH = 210; // A4 width in mm for jsPDF default units
        const MARGIN_X = 15;
        const AVAILABLE = PAGE_WIDTH - MARGIN_X * 2; // 180mm
        const COL_WIDTH = AVAILABLE / 3; // 60mm each
        const COL_LEXEME_X = MARGIN_X;             // 15
        const COL_TOKEN_X = MARGIN_X + COL_WIDTH;  // 75
        const COL_POS_X   = MARGIN_X + COL_WIDTH * 2; // 135
        let y = 50;
        doc.setFontSize(10);
        doc.setFont('courier', 'bold');
        doc.text('Lexeme', COL_LEXEME_X, y);
        doc.text('Token', COL_TOKEN_X, y);
        doc.text('Position', COL_POS_X, y);
        
        y += 5;
        doc.setLineWidth(0.5);
        doc.line(MARGIN_X - 5, y, PAGE_WIDTH - (MARGIN_X - 5), y);
        y += 5;
        
        // Token rows
        doc.setFont('courier', 'normal');
        doc.setFontSize(9);
        
        currentTokens.forEach((token) => {
            if (y > 270) { // New page if needed
                doc.addPage();
                y = 20;
                // Reprint headers on new page
                doc.setFontSize(10);
                doc.setFont('courier', 'bold');
                doc.text('Lexeme', COL_LEXEME_X, y);
                doc.text('Token', COL_TOKEN_X, y);
                doc.text('Position', COL_POS_X, y);
                y += 5;
                doc.setLineWidth(0.5);
                doc.line(MARGIN_X - 5, y, PAGE_WIDTH - (MARGIN_X - 5), y);
                y += 5;
                doc.setFont('courier', 'normal');
                doc.setFontSize(9);
            }
            
            // Truncate long lexemes for layout
            const lexeme = truncateToWidth(token.lexeme, COL_WIDTH - 4, doc);
            const typeText = truncateToWidth(token.type, COL_WIDTH - 4, doc);
            const posText = truncateToWidth(`L${token.line}:C${token.column}`, COL_WIDTH - 4, doc);

            // Render each column within its box to keep spacing equal
            doc.text(lexeme, COL_LEXEME_X, y);
            doc.text(typeText, COL_TOKEN_X, y);
            doc.text(posText, COL_POS_X, y);
            
            y += 6;
        });
        
        try {
            // Primary save path
        doc.save(`${getOutputBaseName()}.pdf`);
        } catch (e) {
            // Fallback for browsers where save is blocked
            try {
                const blob = doc.output('blob');
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${currentFileName}_tokens.pdf`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            } catch (fallbackErr) {
                console.error('PDF fallback failed:', fallbackErr);
                alert('Unable to download PDF. Please use TXT download instead.');
                return;
            }
        }
        
        // Animate button
        downloadPdfBtn.style.transform = 'scale(0.95)';
        setTimeout(() => downloadPdfBtn.style.transform = '', 150);
    }

    // Add smooth scroll to results
    codeInput.addEventListener('input', () => {
        if (resultsPanel.classList.contains('hidden')) {
            setTimeout(() => {
                resultsPanel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            }, 300);
        }
    });
});

