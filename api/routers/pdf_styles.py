STYLESHEET = """
@page {
    size: A4;
    margin: 2cm;
}

body {
    font-family: 'Lato', sans-serif;
    line-height: 1.8;
    color: #333;
    counter-reset: h2;
}

h1, h2, h3, h4, h5, h6 {
    font-weight: 700;
    color: #1976d2;
}

h1 {
    font-size: 2.5em; /* h3 */
    margin-top: 2em;
    margin-bottom: 1.5em;
    font-weight: 700;
    color: #1976d2;
    border-bottom: 2px solid #64b5f6;
    padding-bottom: 0.5em;
}

h2 {
    font-size: 2em; /* h4 */
    margin-top: 1.5em;
    margin-bottom: 1em;
    font-weight: 600;
    color: #212121;
    border-bottom: 1px solid #e0e0e0;
    padding-bottom: 0.3em;
    counter-reset: h3;
    counter-increment: h2;
}
h2:before {
    content: counter(h2) ". ";
}

h3 {
    font-size: 1.5em; /* h5 */
    margin-top: 1.25em;
    margin-bottom: 0.75em;
    font-weight: 600;
    color: #212121;
    counter-reset: h4;
    counter-increment: h3;
}
h3:before {
    content: counter(h2) "." counter(h3) ". ";
}

h4 {
    font-size: 1.2em; /* h6 */
    margin-top: 1em;
    margin-bottom: 0.5em;
    font-weight: 500;
    counter-increment: h4;
}
h4:before {
    content: counter(h2) "." counter(h3) "." counter(h4) ". ";
}

p {
    margin-bottom: 1.25em;
}

strong {
    font-weight: 700;
    color: #1976d2;
}

em {
    font-style: italic;
    color: #616161;
}

ul {
    list-style-type: none;
    padding-left: 0;
    margin-bottom: 1.25em;
}

ul li {
    padding-left: 1.5em;
    position: relative;
    margin-bottom: 0.5em;
}

ul li::before {
    content: '•';
    color: #1976d2;
    font-size: 1.2em;
    position: absolute;
    left: 0;
    top: -0.1em;
}

ol {
    padding-left: 2em;
    margin-bottom: 1.25em;
    counter-reset: item;
}

ol > li {
    display: block;
    margin-bottom: 0.5em;
    position: relative;
}

ol > li:before {
    content: counter(item) ". ";
    counter-increment: item;
    position: absolute;
    left: -2em;
    color: #1976d2;
    font-weight: bold;
}

blockquote {
    border-left: 5px solid #1976d2;
    padding: 1em 1.5em;
    margin: 1.5em 0;
    background-color: rgba(25, 118, 210, 0.04);
    position: relative;
    font-style: italic;
}

/* GitHub-style alerts */
.alert {
    padding: 1em 1.5em;
    margin-bottom: 1.5em;
    border-left-width: 5px;
    border-left-style: solid;
    border-radius: 4px;
}

.alert-note {
    border-color: #64b5f6;
    background-color: #e3f2fd;
}
.alert-tip {
    border-color: #81c784;
    background-color: #e8f5e9;
}
.alert-important {
    border-color: #e57373;
    background-color: #ffebee;
}
.alert-warning, .alert-caution {
    border-color: #ffb74d;
    background-color: #fff8e1;
}

.alert-title {
    font-weight: 600;
    margin-bottom: 0.5em;
    font-size: 0.9em;
    text-transform: uppercase;
}

code {
    background-color: rgba(0, 0, 0, 0.06);
    border-radius: 3px;
    padding: 0.2em 0.4em;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 0.875em;
    border: 1px solid #e0e0e0;
}

pre {
    background-color: #f5f5f5;
    border: 1px solid #e0e0e0;
    padding: 1em;
    margin: 1.5em 0;
    overflow-x: auto;
    border-radius: 4px;
}

pre code {
    background-color: transparent;
    border: none;
    padding: 0;
}

hr {
    border: 0;
    height: 2px;
    background-color: #64b5f6;
    text-align: center;
    margin: 2.5em 0;
    overflow: visible;
}

hr:before {
    content: '•••';
    display: inline-block;
    background: #fff;
    padding: 0 0.5em;
    position: relative;
    top: -0.7em;
    color: #1976d2;
    font-weight: bold;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 1.5em 0;
    border: 1px solid #e0e0e0;
}

th, td {
    border: 1px solid #e0e0e0;
    padding: 0.75em;
    text-align: left;
}

thead {
    background-color: rgba(0, 0, 0, 0.03);
}

th {
    font-weight: 700;
    color: #1976d2;
    font-size: 0.875em;
    text-transform: uppercase;
}
"""