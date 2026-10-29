Run a page's function once on the product reader against the real tables before offering it as a tool there: an inner read of another schema is refused on that login, so close that read quietly rather than fail the tool.
area: products/board, chat, product reader, docstore, tools

Why: board-15 offered `dossier.gather` to the chat model as a tool on the product reader (ruling 122: pub only). Its last step reads the store's records through `support.docstore.landing.documents_of`, which queries `docs.documents`; the product reader is refused (`InsufficientPrivilege`) and every dossier the model asked for failed. The pure tests could not see it: they never open a connection. A probe on the real tables did, before any code was written around it.

How to apply: for each board function reused under another login, run it once on that login against the real tables (a scratch probe script) before wiring it up. Where one inner read needs a grant the login lacks, close that read (`document.records` now returns None on `InsufficientPrivilege` alone, so the documents read closed) rather than widen the login.
