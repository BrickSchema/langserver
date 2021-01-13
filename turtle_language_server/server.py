import asyncio
import re
import uuid
import time
import logging
import io
from urllib.parse import unquote, urlparse
import rdflib
from rdflib.util import guess_format
from rdflib.plugins.parsers.notation3 import BadSyntax
from pygls.server import LanguageServer
from pygls.features import (COMPLETION, TEXT_DOCUMENT_DID_CHANGE,
                            TEXT_DOCUMENT_DID_CLOSE, TEXT_DOCUMENT_DID_OPEN,
                            TEXT_DOCUMENT_DID_SAVE)
from pygls.server import LanguageServer
from pygls.types import (CompletionItem, CompletionList, CompletionParams,
                         ConfigurationItem, ConfigurationParams, Diagnostic,
                         DidChangeTextDocumentParams,
                         DidCloseTextDocumentParams, DidOpenTextDocumentParams,
                         DidSaveTextDocumentParams,
                         MessageType, Position, Range, Registration,
                         RegistrationParams, Unregistration,
                         UnregistrationParams)

COUNT_DOWN_START_IN_SECONDS = 10
COUNT_DOWN_SLEEP_IN_SECONDS = 1

logging.basicConfig(filemode='w', level=logging.DEBUG)


class TurtleLanguageServer(LanguageServer):
    CMD_COUNT_DOWN_BLOCKING = 'countDownBlocking'
    CMD_COUNT_DOWN_NON_BLOCKING = 'countDownNonBlocking'
    CMD_REGISTER_COMPLETIONS = 'registerCompletions'
    CMD_SHOW_CONFIGURATION_ASYNC = 'showConfigurationAsync'
    CMD_SHOW_CONFIGURATION_CALLBACK = 'showConfigurationCallback'
    CMD_SHOW_CONFIGURATION_THREAD = 'showConfigurationThread'
    CMD_LOAD_GRAPHS = 'loadGraphs'
    CMD_UNREGISTER_COMPLETIONS = 'unregisterCompletions'

    CONFIGURATION_SECTION = 'ttlServer'
    graph = rdflib.Graph()
    nsgraphs = {}

    def __init__(self):
        super().__init__()


ttl_server = TurtleLanguageServer()


def _load(ls, params):
    ls.show_message_log('Updating graph...')
    text_doc = ls.workspace.get_document(params.textDocument.uri)
    source = text_doc.source

    # reinitialize graph
    ls.graph = rdflib.Graph()
    ls.graph.parse(source=io.StringIO(source), format="ttl")
    load_stuff(ls)


@ttl_server.thread()
@ttl_server.command(TurtleLanguageServer.CMD_LOAD_GRAPHS)
def load_stuff(ls: TurtleLanguageServer, *args):
    namespaces = list(ls.graph.namespaces())
    force = 'force' in args[0] if len(args) > 0 else False
    for pfx, namespace in namespaces:
        if not force and (pfx in ls.nsgraphs and len(ls.nsgraphs[pfx]) > 0):
            continue
        try:
            ls.show_message_log(f"Loading graph {namespace} for prefix {pfx}")
            ls.nsgraphs[pfx] = rdflib.Graph()
            ls.nsgraphs[pfx] = ls.graph.parse(namespace, format=guess_format(namespace))
            ls.show_message(f"Loaded graph {pfx} = {namespace}")
            print(len(ls.nsgraphs[pfx]))
        except Exception as e:
            print(e)
            continue


def _validate(ls, params):
    ls.show_message_log('Validating turtle...')

    text_doc = ls.workspace.get_document(params.textDocument.uri)

    source = text_doc.source
    diagnostics = _validate_ttl(source) if source else []
    ls.show_message_log(diagnostics)
    ls.publish_diagnostics(text_doc.uri, diagnostics)


def _validate_ttl(source):
    diagnostics = []
    try:
        g = rdflib.Graph()
        g.parse(source=io.StringIO(source), format="ttl")
    except BadSyntax as e:
        (uri, lines, argstr, i, why) = e.args
        d = Diagnostic(
                Range(
                    Position(e.lines-1, 0),
                    Position(e.lines, 0)
                ),
                why,
                source=type(ttl_server).__name__)
        diagnostics.append(d)
    except Exception as e:
        print(e, type(e))
        print(dir(e))
    return diagnostics

def to_os_path(uri):
    return unquote(urlparse(uri).path)


@ttl_server.feature(COMPLETION, trigger_characters=[':'])
def completions(ls: TurtleLanguageServer, params: CompletionParams = None):
    """Returns completion items."""
    print("COMPLETION", params)
    line = params.position.line
    char = params.position.character
    doc = io.StringIO(ls.workspace.get_document(params.textDocument.uri).source)
    [doc.readline() for l in range(line)]
    line = doc.readline()
    pfx = re.findall(r"\s*(\w+):", line[:char])
    if len(pfx) == 0:
        return CompletionList(False, [])
    pfx = pfx[-1] # get the last one(?)
    ns = ls.graph.store.namespace(pfx)
    print(pfx, ns, ls.nsgraphs.get(pfx))
    if pfx is None or ns is None:
        return CompletionList(False, [])
    g = ls.nsgraphs.get(pfx, rdflib.Graph())
    print("autocomplete for", pfx, ns, len(g))
    subjects = [str(x)[len(ns):] for x in g.subjects() if not isinstance(x, rdflib.BNode) and str(x).startswith(ns)]
    subjects = list(set(subjects))
    return CompletionList(False, [CompletionItem(x) for x in subjects])


@ttl_server.command(TurtleLanguageServer.CMD_COUNT_DOWN_BLOCKING)
def count_down_10_seconds_blocking(ls, *args):
    """Starts counting down and showing message synchronously.
    It will `block` the main thread, which can be tested by trying to show
    completion items.
    """
    for i in range(COUNT_DOWN_START_IN_SECONDS):
        ls.show_message('Counting down... {}'
                        .format(COUNT_DOWN_START_IN_SECONDS - i))
        time.sleep(COUNT_DOWN_SLEEP_IN_SECONDS)


@ttl_server.command(TurtleLanguageServer.CMD_COUNT_DOWN_NON_BLOCKING)
async def count_down_10_seconds_non_blocking(ls, *args):
    """Starts counting down and showing message asynchronously.
    It won't `block` the main thread, which can be tested by trying to show
    completion items.
    """
    for i in range(COUNT_DOWN_START_IN_SECONDS):
        ls.show_message('Counting down... {}'
                        .format(COUNT_DOWN_START_IN_SECONDS - i))
        await asyncio.sleep(COUNT_DOWN_SLEEP_IN_SECONDS)


@ttl_server.feature(TEXT_DOCUMENT_DID_CHANGE)
def did_change(ls, params: DidChangeTextDocumentParams):
    """Text document did change notification."""
    load_stuff(ls)


@ttl_server.feature(TEXT_DOCUMENT_DID_CLOSE)
def did_close(server: TurtleLanguageServer, params: DidCloseTextDocumentParams):
    """Text document did close notification."""
    server.show_message('Text Document Did Close')


@ttl_server.feature(TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls, params: DidOpenTextDocumentParams):
    """Text document did open notification."""
    # ls.show_message('Text Document Did Open')
    _validate(ls, params)
    _load(ls, params)


@ttl_server.feature(TEXT_DOCUMENT_DID_SAVE)
async def did_save(ls, params):
    """Text document did save notification."""
    # ls.show_message('Text Document Did Save')
    _validate(ls, params)
    _load(ls, params)


@ttl_server.command(TurtleLanguageServer.CMD_REGISTER_COMPLETIONS)
async def register_completions(ls: TurtleLanguageServer, *args):
    """Register completions method on the client."""
    params = RegistrationParams([Registration(str(uuid.uuid4()), COMPLETION,
                                              {"triggerCharacters": "[':']"})])
    response = await ls.register_capability_async(params)
    if response is None:
        ls.show_message('Successfully registered completions method')
    else:
        ls.show_message('Error happened during completions registration.',
                        MessageType.Error)

if __name__ == '__main__':
    ttl_server.start_tcp('localhost', 8080)
# ttl_server.start_io()
