# Turtle Language Server

This is a [LSP server](https://langserver.org/) implementation for RDF graphs serialized as Turtle.

Install with: `pip install turtle_language_server`


## With NeoVim and CoC

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
