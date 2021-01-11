# Turtle Language Server

[![PyPI version](https://badge.fury.io/py/turtle_language_server.svg)](https://badge.fury.io/py/turtle_language_server)

This is a [LSP server](https://langserver.org/) implementation for RDF graphs serialized as Turtle.

Install with: `pip install turtle_language_server`

## Commands and Features

- Use the `loadGraphs` command to pull in the graph definitions listed as prefixes in your Turtle file:
    ```
    # caches graphs in-memory for NeoVim session
    :CocCommand loadGraphs
    ```
    
    ```
    # overrides cache and pulls graphs anyway
    :CocCommand loadGraphs force
    ```
- syntax checking your Turtle file (including undefined namespaces)
- auto-complete when adding statements to the file (relies on `loadGraphs`)

## TODOs:

- [ ] verify shapes and add validation information to UI


## Setup With NeoVim and CoC

If you are using [`coc.nvim`](https://github.com/neoclide/coc.nvim), you can configure the language server as follows:

1. Make sure Vim correctly detects turtle files and sets the filetype. One way to achieve this
   is by adding the following line to your `.vimrc` or `init.nvim`:

   ```vimrc
   au BufRead,BufNewFile *.ttl set filetype=turtle
   ```
2. Modify your CoC settings to use the `turtle_language_server` when you open a Turtle file.
    1. First, run `:CocConfig` or edit `coc-settings.json`
    2. Add the following (merge with existing keys in `"languageserver"` if needed):
        ```json
        {
          "languageserver": {
            "turtle": {
              "command": "turtle_langserver",
              "filetypes": ["ttl", "turtle"]
            }
          }
        }
        ```
