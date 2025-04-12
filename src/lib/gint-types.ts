import * as monaco from 'monaco-editor';

export const gintSymbols: any[] = [
	{
		label: 'getkey',
		kind: monaco.languages.CompletionItemKind.Function,
		documentation: "Blocking key wait with repeat simulation\n\nReturns: KeyEvent",
		insertText: 'getkey()',
		detail: 'function'
	},
	{
		label: 'C_WHITE',
		kind: monaco.languages.CompletionItemKind.Constant,
		documentation: "White color constant (value: 0xFFFF)",
		detail: 'constant'
	},
	// Add all symbols with proper types and docs
	{
		label: 'KeyEvent',
		kind: monaco.languages.CompletionItemKind.Class,
		documentation: `Key event structure:
- time: int (timestamp)
- key: int (key code)
- type: int (event type)
- mod: bool (modifier state)`,
		detail: 'class'
	},
	// ... complete the list with all your exports ...
];