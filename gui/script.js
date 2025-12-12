// Modern SQL Lexer GUI - Interactive JavaScript

document.addEventListener('DOMContentLoaded', () => {
    const codeInput = document.getElementById('codeInput');
    const actionBtn = document.getElementById('actionBtn');
    const tokenizeTab = document.getElementById('tokenizeTab');
    const parseTab = document.getElementById('parseTab');
    const clearBtn = document.getElementById('clearBtn');
    const fileUpload = document.getElementById('fileUpload');
    const downloadTxtBtn = document.getElementById('downloadTxtBtn');
    const downloadPdfBtn = document.getElementById('downloadPdfBtn');
    const resultsPanel = document.getElementById('resultsPanel');
    const resultsContainer = document.getElementById('resultsContainer');
    const parseTreeContainer = document.getElementById('parseTreeContainer');
    const parseTree = document.getElementById('parseTree');
    const visualTree = document.getElementById('visualTree');
    const treeSvg = document.getElementById('treeSvg');
    const textTreeBtn = document.getElementById('textTreeBtn');
    const visualTreeBtn = document.getElementById('visualTreeBtn');
    const errorContainer = document.getElementById('errorContainer');
    const errorsList = document.getElementById('errorsList');
    const noResults = document.getElementById('noResults');
    const tokenCount = document.getElementById('tokenCount');
    const analysisMode = document.getElementById('analysisMode');
    
    // Store current tokens for download
    let currentTokens = [];
    let currentFileName = 'tokens';
    let currentMode = 'tokenize'; // 'tokenize' or 'parse'
    let currentParseTree = null; // Store parse tree data

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

    // Tab switching
    tokenizeTab.addEventListener('click', () => {
        currentMode = 'tokenize';
        tokenizeTab.classList.add('active');
        parseTab.classList.remove('active');
        actionBtn.querySelector('.btn-text').textContent = 'Tokenize';
        analysisMode.style.display = 'block';
        hideResults();
    });

    parseTab.addEventListener('click', () => {
        currentMode = 'parse';
        parseTab.classList.add('active');
        tokenizeTab.classList.remove('active');
        actionBtn.querySelector('.btn-text').textContent = 'Parse';
        analysisMode.style.display = 'none';
        hideResults();
    });

    // Keyboard shortcuts
    codeInput.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            if (currentMode === 'tokenize') {
                tokenizeCode();
            } else {
                parseCode();
            }
        }
    });

    // Action button event
    actionBtn.addEventListener('click', () => {
        if (currentMode === 'tokenize') {
            tokenizeCode();
        } else {
            parseCode();
        }
    });

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
                // Auto process after upload
                if (currentMode === 'tokenize') {
                tokenizeCode();
                } else {
                    parseCode();
                }
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
            
            const errorType = error.type || 'lexical';
            const errorTypeLabel = errorType === 'syntax' ? 'Syntax Error' : 'Lexical Error';
            
            errorBox.innerHTML = `
                <div class="error-icon">⚠️</div>
                <div class="error-content">
                    <h3>${errorTypeLabel} ${errors.length > 1 ? `#${index + 1}` : ''}</h3>
                    <p>${escapeHtml(message)}</p>
                    ${line && col ? `<div class="error-position">Line ${line}, Column ${col}</div>` : ''}
                    ${error.expected && error.found ? `<div class="error-detail">Expected: ${escapeHtml(error.expected)}, Found: ${escapeHtml(error.found)}</div>` : ''}
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
        parseTreeContainer.classList.add('hidden');
    }

    // Parse function
    async function parseCode() {
        const code = codeInput.value.trim();
        
        if (!code) {
            showError('Please enter some code to parse');
            return;
        }

        // Show loading state
        setLoading(true);
        hideResults();
        
        try {
            const response = await fetch('/parse', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ code })
            });

            const data = await response.json();
            
            if (data.success) {
                showParseTree(data.parseTree);
                tokenCount.textContent = 'Parse successful';
                downloadTxtBtn.classList.add('hidden');
                downloadPdfBtn.classList.add('hidden');
            } else {
                // Handle errors
                if (data.errors && Array.isArray(data.errors)) {
                    showErrors(data.errors);
                    // If parse tree is available despite errors, show it
                    if (data.parseTree) {
                        showParseTree(data.parseTree);
                    }
                } else if (data.error) {
                    showError(data.error);
                } else {
                    showError('An unknown error occurred');
                }
            }
        } catch (error) {
            showError('An error occurred while parsing. Please try again.');
            console.error('Error:', error);
        } finally {
            setLoading(false);
        }
    }

    // Show parse tree
    function showParseTree(tree) {
        noResults.classList.add('hidden');
        resultsContainer.classList.add('hidden');
        errorContainer.classList.add('hidden');
        parseTreeContainer.classList.remove('hidden');
        
        currentParseTree = tree; // Store tree data
        
        // Show text view by default
        showTextView();
    }
    
    // Show text view
    function showTextView() {
        parseTree.classList.remove('hidden');
        visualTree.classList.add('hidden');
        textTreeBtn.classList.add('active');
        visualTreeBtn.classList.remove('active');
        
        if (currentParseTree) {
            parseTree.innerHTML = renderParseTree(currentParseTree, 0);
        }
    }
    
    // Show visual tree view
    function showVisualTree() {
        parseTree.classList.add('hidden');
        visualTree.classList.remove('hidden');
        textTreeBtn.classList.remove('active');
        visualTreeBtn.classList.add('active');
        
        if (currentParseTree) {
            renderVisualTree(currentParseTree);
        }
    }
    
    // Toggle button events
    textTreeBtn.addEventListener('click', showTextView);
    visualTreeBtn.addEventListener('click', showVisualTree);
    

    // Render parse tree recursively with proper tree structure
    function renderParseTree(node, level = 0, isLast = true, prefix = '', isRoot = true) {
        if (!node) return '';
        
        const nodeType = node.nodeType || '';
        const token = node.token || null;
        const children = node.children || [];
        const validChildren = children.filter(child => typeof child === 'object' && child !== null && child.nodeType);
        
        // Determine tree connectors
        const connector = isRoot ? '' : (isLast ? '└─ ' : '├─ ');
        const spacer = isRoot ? '' : (isLast ? '   ' : '│  ');
        
        let html = '<div class="parse-tree-item">';
        
        // Tree line with connector (always show for non-root, or show root differently)
        if (isRoot) {
            // Root node - no connector, but styled differently
            html += `<span class="parse-tree-node" data-level="${level}">`;
            html += `<span class="parse-tree-node-type">${escapeHtml(nodeType)}</span>`;
        } else {
            // Child nodes - show connector
            html += `<span class="parse-tree-line">${prefix}${connector}</span>`;
            html += `<span class="parse-tree-node" data-level="${level}">`;
            html += `<span class="parse-tree-node-type">${escapeHtml(nodeType)}</span>`;
        }
        
        if (token) {
            html += ` <span class="parse-tree-node-token">[${escapeHtml(token.lexeme)}]</span>`;
        }
        
        // Add expand/collapse button if has children
        if (validChildren.length > 0) {
            html += ` <span class="parse-tree-toggle" onclick="toggleTreeNode(this)">▼</span>`;
        }
        
        html += '</span>';
        html += '</div>';
        
        // Render children
        if (validChildren.length > 0) {
            html += `<div class="parse-tree-children">`;
            for (let i = 0; i < validChildren.length; i++) {
                const child = validChildren[i];
                const isChildLast = i === validChildren.length - 1;
                const childPrefix = isRoot ? '' : prefix + spacer;
                html += renderParseTree(child, level + 1, isChildLast, childPrefix, false);
            }
            html += `</div>`;
        }
        
        return html;
    }
    
    // Toggle tree node expansion
    window.toggleTreeNode = function(button) {
        const item = button.closest('.parse-tree-item');
        const children = item.nextElementSibling;
        if (children && children.classList.contains('parse-tree-children')) {
            const isExpanded = children.style.display !== 'none';
            children.style.display = isExpanded ? 'none' : 'block';
            button.textContent = isExpanded ? '▶' : '▼';
            button.classList.toggle('collapsed', isExpanded);
        }
    };
    
    // Render visual tree diagram (top to bottom)
    function renderVisualTree(tree) {
        if (!tree) return;
        
        // Clear previous tree
        treeSvg.innerHTML = '';
        
        // Calculate tree dimensions (optimized spacing for better visual balance)
        const nodeWidth = 140;
        const nodeHeight = 65;
        const horizontalSpacing = 140;  // Balanced spacing
        const verticalSpacing = 100;    // Balanced spacing
        
        // Build tree structure
        const treeData = buildTreeData(tree);
        if (!treeData) return;
        
        // Calculate positions for all nodes
        const positions = calculatePositions(treeData, nodeWidth, nodeHeight, horizontalSpacing, verticalSpacing);
        
        // Calculate SVG dimensions based on actual positions
        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        positions.forEach(pos => {
            minX = Math.min(minX, pos.x);
            maxX = Math.max(maxX, pos.x);
            minY = Math.min(minY, pos.y);
            maxY = Math.max(maxY, pos.y);
        });
        
        const padding = 50;
        const svgWidth = Math.max(900, maxX - minX + nodeWidth + padding * 2);
        const svgHeight = maxY + nodeHeight + padding * 2;
        
        // Adjust positions to account for padding
        const offsetX = padding - minX + nodeWidth / 2;
        const offsetY = padding;
        
        positions.forEach((pos, id) => {
            positions.set(id, {
                x: pos.x + offsetX,
                y: pos.y + offsetY
            });
        });
        
        treeSvg.setAttribute('width', svgWidth);
        treeSvg.setAttribute('height', svgHeight);
        treeSvg.setAttribute('viewBox', `0 0 ${svgWidth} ${svgHeight}`);
        
        // Draw connections first (so they appear behind nodes)
        drawConnections(treeData, positions, nodeWidth, nodeHeight);
        
        // Draw nodes
        drawNodes(treeData, positions, nodeWidth, nodeHeight);
    }
    
    // Build tree data structure
    function buildTreeData(node) {
        if (!node) return null;
        
        const nodeType = node.nodeType || '';
        const token = node.token || null;
        const children = (node.children || []).filter(child => 
            typeof child === 'object' && child !== null && child.nodeType
        );
        
        return {
            id: Math.random().toString(36).substr(2, 9),
            name: nodeType,
            token: token ? token.lexeme : null,
            children: children.map(child => buildTreeData(child)).filter(child => child !== null)
        };
    }
    
    // Get maximum depth of tree
    function getMaxDepth(node) {
        if (!node || !node.children || node.children.length === 0) {
            return 0;
        }
        return 1 + Math.max(...node.children.map(child => getMaxDepth(child)));
    }
    
    // Get maximum width of tree
    function getMaxWidth(node) {
        if (!node || !node.children || node.children.length === 0) {
            return 1;
        }
        return node.children.reduce((sum, child) => sum + getMaxWidth(child), 0);
    }
    
    // Calculate positions for all nodes using improved algorithm
    function calculatePositions(node, nodeWidth, nodeHeight, hSpacing, vSpacing) {
        const positions = new Map();
        let nextX = 100;
        
        function layout(node, depth, xStart) {
            if (!node) return { x: xStart, width: 0 };
            
            const y = depth * vSpacing + 50;
            
            if (!node.children || node.children.length === 0) {
                // Leaf node
            const x = nextX;
            nextX += hSpacing;
            positions.set(node.id, { x, y });
            return { x, width: hSpacing }; // Balanced spacing
            }
            
            // Layout children first
            let childrenStartX = nextX;
            let childrenEndX = nextX;
            
            for (const child of node.children) {
                const childLayout = layout(child, depth + 1, nextX);
                childrenEndX = childLayout.x + childLayout.width;
                nextX = childrenEndX;
            }
            
            // Position parent in center of children
            const parentX = (childrenStartX + childrenEndX) / 2;
            positions.set(node.id, { x: parentX, y });
            
            return { x: parentX, width: childrenEndX - childrenStartX };
        }
        
        layout(node, 0, 100);
        return positions;
    }
    
    // Draw connections between nodes
    function drawConnections(node, positions, nodeWidth, nodeHeight) {
        if (!node || !node.children || node.children.length === 0) return;
        
        const nodePos = positions.get(node.id);
        if (!nodePos) return;
        
        const parentX = nodePos.x;
        const parentY = nodePos.y + nodeHeight;
        
        // Draw horizontal line above children if multiple children
        if (node.children.length > 1) {
            const firstChildX = positions.get(node.children[0].id)?.x || parentX;
            const lastChildX = positions.get(node.children[node.children.length - 1].id)?.x || parentX;
            const midY = nodePos.y + nodeHeight + 20;
            
            const hLine = document.createElementNS('http://www.w3.org/2000/svg', 'line');
            hLine.setAttribute('x1', firstChildX);
            hLine.setAttribute('y1', midY);
            hLine.setAttribute('x2', lastChildX);
            hLine.setAttribute('y2', midY);
            hLine.setAttribute('stroke', 'rgba(102, 126, 234, 0.65)');
            hLine.setAttribute('stroke-width', '2.5');
            treeSvg.appendChild(hLine);
        }
        
        // Draw line to each child
        node.children.forEach(child => {
            const childPos = positions.get(child.id);
            if (childPos) {
                const childX = childPos.x;
                const childY = childPos.y;
                const midY = nodePos.y + nodeHeight + 20;
                
                // Vertical line from parent to mid point
                const line1 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line1.setAttribute('x1', parentX);
                line1.setAttribute('y1', parentY);
                line1.setAttribute('x2', parentX);
                line1.setAttribute('y2', midY);
                line1.setAttribute('stroke', 'rgba(102, 126, 234, 0.65)');
                line1.setAttribute('stroke-width', '2.5');
                treeSvg.appendChild(line1);
                
                // Horizontal line to child (if multiple children)
                if (node.children.length > 1) {
                    const line2 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                    line2.setAttribute('x1', parentX);
                    line2.setAttribute('y1', midY);
                    line2.setAttribute('x2', childX);
                    line2.setAttribute('y2', midY);
                    line2.setAttribute('stroke', 'rgba(102, 126, 234, 0.65)');
                    line2.setAttribute('stroke-width', '2.5');
                    treeSvg.appendChild(line2);
                }
                
                // Vertical line to child
                const line3 = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                line3.setAttribute('x1', childX);
                line3.setAttribute('y1', midY);
                line3.setAttribute('x2', childX);
                line3.setAttribute('y2', childY);
                line3.setAttribute('stroke', 'rgba(102, 126, 234, 0.65)');
                line3.setAttribute('stroke-width', '2.5');
                treeSvg.appendChild(line3);
            }
            
            // Recursively draw connections for children
            drawConnections(child, positions, nodeWidth, nodeHeight);
        });
    }
    
    // Draw nodes
    function drawNodes(node, positions, nodeWidth, nodeHeight) {
        if (!node) return;
        
        const pos = positions.get(node.id);
        if (!pos) return;
        
        const x = pos.x - nodeWidth / 2;
        const y = pos.y;
        
        // Node rectangle with gradient effect
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', x);
        rect.setAttribute('y', y);
        rect.setAttribute('width', nodeWidth);
        rect.setAttribute('height', nodeHeight);
        rect.setAttribute('rx', '10');
        rect.setAttribute('fill', 'rgba(102, 126, 234, 0.15)');
        rect.setAttribute('stroke', 'rgba(102, 126, 234, 0.9)');
        rect.setAttribute('stroke-width', '2.5');
        rect.setAttribute('class', 'tree-node-rect');
        treeSvg.appendChild(rect);
        
        // Node type text
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', pos.x);
        text.setAttribute('y', y + (node.token ? 24 : nodeHeight / 2 + 5));
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('fill', '#ff6b9d');
        text.setAttribute('font-size', '13');
        text.setAttribute('font-weight', '600');
        text.setAttribute('font-family', 'Fira Code, monospace');
        
        // Truncate long node names
        const displayName = node.name.length > 16 ? node.name.substring(0, 13) + '...' : node.name;
        text.textContent = displayName;
        treeSvg.appendChild(text);
        
        // Token text if available
        if (node.token) {
            const tokenText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            tokenText.setAttribute('x', pos.x);
            tokenText.setAttribute('y', y + nodeHeight - 12);
            tokenText.setAttribute('text-anchor', 'middle');
            tokenText.setAttribute('fill', '#ffcb6b');
            tokenText.setAttribute('font-size', '11');
            tokenText.setAttribute('font-style', 'italic');
            tokenText.setAttribute('font-family', 'Fira Code, monospace');
            
            // Truncate long tokens
            const displayToken = node.token.length > 13 ? node.token.substring(0, 10) + '...' : node.token;
            tokenText.textContent = `[${displayToken}]`;
            treeSvg.appendChild(tokenText);
        }
        
        // Recursively draw child nodes
        if (node.children) {
            node.children.forEach(child => drawNodes(child, positions, nodeWidth, nodeHeight));
        }
    }

    // Set loading state
    function setLoading(loading) {
        if (loading) {
            actionBtn.classList.add('loading');
            actionBtn.disabled = true;
        } else {
            actionBtn.classList.remove('loading');
            actionBtn.disabled = false;
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

