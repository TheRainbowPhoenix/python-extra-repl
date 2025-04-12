<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import * as monaco from "monaco-editor";
  import editorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";

  import { code as pyCode } from "./lib/py_code";
  import { gintSymbols } from "./lib/gint-types";
  import Preview from "./lib/Preview.svelte";

  //   let pyscriptFrame: HTMLIFrameElement;
  let editorCode = pyCode;

  let editorElement: HTMLDivElement;
  let editor: monaco.editor.IStandaloneCodeEditor;
  let model: monaco.editor.ITextModel;

  type CompletionItem = monaco.languages.CompletionItem;
  type CompletionList = monaco.languages.CompletionList;

  let disabled = false;

  function loadCode(code: string, language: string) {
    model = monaco.editor.createModel(code, language);

    editor.setModel(model);
  }

  const createPythonCompletionProvider =
    (): monaco.languages.CompletionItemProvider => ({
      triggerCharacters: [".", "("],
      provideCompletionItems: (model, position) => {
        const word = model.getWordAtPosition(position);
        const line = model.getLineContent(position.lineNumber);

        // Show all symbols when typing in global scope
        return {
          suggestions: gintSymbols.map((symbol) => ({
            ...symbol,
            range: new monaco.Range(
              position.lineNumber,
              word?.startColumn || position.column,
              position.lineNumber,
              word?.endColumn || position.column
            ),
          })),
        };
      },
    });

  // PyScript management
  let currentPyScript: any = null;

  function runCode() {
    // if (!pyscriptFrame) return;
	if (disabled) return;

	disabled = true;

    let code = editor.getValue();
    console.log(code);

    if (currentPyScript) {
      currentPyScript.remove();
      // Clear PyScript internal state
      // @ts-ignore
      if (window.pyodide) {
        // @ts-ignore
        window.pyodide._api.finalizeBootstrap(); // @ts-ignore
        window.pyodide = null;
      }
    }

    // Create new script element
    const script = document.createElement("script");
    script.type = "py";
    script.textContent = code;
    document.body.appendChild(script);
    currentPyScript = script;

    // Reinitialize PyScript
    setTimeout(() => {
      window.dispatchEvent(new Event("DOMContentLoaded"));
      window.dispatchEvent(new CustomEvent("py:restart"));
    }, 100);
  }

  onMount(async () => {
    self.MonacoEnvironment = {
      getWorker: function (_: any, label: string) {
        return new editorWorker();
      },
    };

	window.addEventListener('py:ready', () => {
		console.log("ready !");
		disabled = false;
	});
    monaco.languages.register({ id: "python" });

    monaco.languages.registerCompletionItemProvider(
      "python",
      createPythonCompletionProvider()
    );

    // monaco.languages.registerSignatureHelpProvider('python', {
    // 	signatureHelpTriggerCharacters: ['('],
    // 	provideSignatureHelp: (model, position) => {
    // 		// Implement parameter hint logic
    // 	}
    // });

    monaco.languages.registerHoverProvider("python", {
      provideHover: (model, position) => {
        const word = model.getWordAtPosition(position);
        const symbol = gintSymbols.find((s) => s.label === word?.word);
        return symbol
          ? {
              contents: [{ value: symbol.documentation }],
            }
          : null;
      },
    });

    // monaco.languages.python.pythonDefaults.setDiagnosticsOptions({
    // 	validate: true,
    // 	linterOptions: {
    // 		// Your validation rules
    // 	}
    // });

    // monaco.languages.typescript.typescriptDefaults.setEagerModelSync(true);

    editor = monaco.editor.create(editorElement, {
      automaticLayout: true,
      theme: "vs-dark",
      language: "python",
      suggest: {
        showFiles: false,
        showWords: false,
      },
    });

    loadCode(pyCode, "python");
  });

  onDestroy(() => {
    monaco?.editor.getModels().forEach((model) => model.dispose());
    editor?.dispose();
  });
</script>

<main>
  <div class="editor">
    <div class="toolbar">
      <!-- <button
        class="w-fit border-2 p-1"
        on:click={() => loadCode(pyCode, "python")}>Python</button
      > -->
      <button on:click={runCode} class="btn-primary run-button" {disabled}>
        Run Code
        <div class="ico">
          <svg
            viewBox="0 0 32 32"
            width="1.2em"
            height="1.2em"
            class="text-base sm:text-xs"
            ><path
              fill="currentColor"
              d="M7 28a1 1 0 0 1-1-1V5a1 1 0 0 1 1.482-.876l20 11a1 1 0 0 1 0 1.752l-20 11A1 1 0 0 1 7 28"
            ></path></svg
          >
        </div>
      </button>
    </div>
    <div class="editorElement" bind:this={editorElement} ></div>
  </div>

  <Preview />
</main>

<style>
  main {
    display: flex;
    height: 100vh;
    width: 100%;
    flex-direction: row;
  }

  .editor {
    display: flex;
    height: 100vh;
    width: 100%;
    flex-direction: column;
  }
  .toolbar {
    display: flex;
    gap: 0.25rem;
    padding: 0.5rem;
    justify-content: center;
  }
  .editorElement {
    flex: 1 1 auto;
  }

  .toolbar button > .ico {
	display: flex;
  }
</style>
