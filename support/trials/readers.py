"""THE READERS UNDER TRIAL (plan step 3.2): each page reader with its own
documented prompt and input format, its compression level, its family and
the scheduler profile that serves it. These models are trained on specific
prompts and do poorly on generic ones, so the prompt is the model's own,
quoted from its model card or its package, never a paraphrase.

    readers.READERS[name]              a Reader
    readers.by_profile(profile_name)   the Reader a scheduler profile serves
    readers.settings(reader, dpi)      what a reading is stamped with (ruling 50)
    readers.messages(reader, b64, mt)  the chat messages for one page image

Families: GLM-OCR (Zhipu, GLM-V encoder-decoder) is one; every Qwen-based
model is the other (TeleOCR on Qwen 2.5-VL with a Qwen3-style decoder;
OvisOCR2, Chandra OCR 2 and Infinity-Parser2-Pro on Qwen 3.5). Two Qwen
models agreeing is weaker confirmation than GLM-OCR agreeing with one.

GLM-OCR is run as the old estate ran it: the bare instruction "OCR" that
ggml-org's guide uses, which the 22 September choice was made on; its model
card's own document-parsing prompt ("Text Recognition:") is a different
setting and is recorded here as a variant, not run in pass one.
"""
from __future__ import annotations

import dataclasses
import hashlib
import os

MODELS = os.environ.get("QV4_TRIAL_MODELS") or "/mnt/hdd2/qv4-models"
OLD_MODELS = "/home/user/models/vision-glm-ocr"

PROMPT_GLM_OCR = "OCR"
PROMPT_GLM_OCR_CARD = "Text Recognition:"
PROMPT_TELEOCR_TEXT = "Please output the text content from the image."
PROMPT_TELEOCR_TABLE = "This is the image of a table. Please output the table in OTSL format."
SYSTEM_TELEOCR = "You are a helpful assistant."
PROMPT_OVISOCR2 = ("Extract all readable content from the image in natural human reading order and output the result as a "
                   "single Markdown document. Format formulas as LaTeX. Format tables as HTML: <table>...</table>. "
                   "Preserve the original text without translation.")
_CHANDRA_TAGS = ["math", "br", "i", "b", "u", "del", "sup", "sub", "table", "tr", "td", "p", "th", "div", "pre", "h1", "h2",
                 "h3", "h4", "h5", "ul", "ol", "li", "input", "a", "span", "img", "hr", "tbody", "small", "caption", "strong",
                 "thead", "big", "code", "chem"]
_CHANDRA_ATTRS = ["class", "colspan", "rowspan", "display", "checked", "type", "border", "value", "style", "href", "alt",
                  "align", "data-bbox", "data-label"]
_CHANDRA_ENDING = f"""
Only use these tags {_CHANDRA_TAGS}, and these attributes {_CHANDRA_ATTRS}.

Guidelines:
* Inline math: Surround math with <math>...</math> tags. Math expressions should be rendered in KaTeX-compatible LaTeX. Use display for block math.
* Tables: Use colspan and rowspan attributes to match table structure.
* Formatting: Maintain consistent formatting with the image, including spacing, indentation, subscripts/superscripts, and special characters.
* Images: Include a description of any images in the alt attribute of an <img> tag. Do not fill out the src property. Describe in detail inside the div tag. Also convert charts to high fidelity data, and convert diagrams to mermaid.
* Forms: Mark checkboxes and radio buttons properly.
* Text: join lines together properly into paragraphs using <p>...</p> tags.  Use <br> tags for line breaks within paragraphs, but only when absolutely necessary to maintain meaning.
* Chemistry: Use <chem>...</chem> tags for chemical formulas with reactive SMILES.
* Lists: Preserve indents and proper list markers.
* Use the simplest possible HTML structure that accurately represents the content of the block.
* Make sure the text is accurate and easy for a human to read and interpret.  Reading order should be correct and natural.
""".strip()
PROMPT_CHANDRA = f"""
OCR this image to HTML, arranged as layout blocks.  Each layout block should be a div with the data-bbox attribute representing the bounding box of the block in x0 y0 x1 y1 format.  Bboxes are normalized 0-1000. The data-label attribute is the label for the block.

Use the following labels:
- Caption
- Footnote
- Equation-Block
- List-Group
- Page-Header
- Page-Footer
- Image
- Section-Header
- Table
- Text
- Complex-Block
- Code-Block
- Form
- Table-Of-Contents
- Figure
- Chemical-Block
- Diagram
- Bibliography
- Blank-Page

{_CHANDRA_ENDING}
""".strip()
PROMPT_INFINITY_DOC2MD = """
You are an AI assistant specialized in converting PDF images to Markdown format. Please follow these instructions for the conversion:

1. Text Processing:
- Accurately recognize all text content in the PDF image without guessing or inferring.
- Convert the recognized text into Markdown format.
- Maintain the original document structure, including headings, paragraphs, lists, etc.

2. Mathematical Formula Processing:
- Convert all mathematical formulas to LaTeX format.
- Enclose inline formulas with $ $. For example: This is an inline formula $E = mc^2$
- Enclose block formulas with $$ $$. For example: $$\\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$

3. Table Processing:
- Convert tables to HTML format.

4. Figure Handling:
- Ignore figures content in the PDF image. Do not attempt to describe or convert images.

5. Output Format:
- Ensure the output Markdown document has a clear structure with appropriate line breaks between elements.
- For complex layouts, try to maintain the original document's structure and format as closely as possible.

Please strictly follow these guidelines to ensure accuracy and consistency in the conversion. Your task is to accurately convert the content of the PDF image into Markdown format without adding any extra explanations or comments.
"""


@dataclasses.dataclass(frozen=True)
class Reader:
    name: str              # the trial's name: model and compression
    model: str             # the alias the server advertises; what every call demands
    profile: str           # the scheduler profile (profiles.toml) that serves it
    family: str            # zhipu | qwen
    level: str             # compression: q8_0, f16, q4_k_m …
    weights: tuple         # absolute paths: the weights, then the image projector
    prompt: str
    prompt_from: str       # where the prompt is documented
    output: str            # markdown | html | otsl | json: how tables come out
    system: str = None     # a system message, only where the model's own example sends one
    thinking_off: bool = False   # Qwen 3.5 bases think unless told not to
    max_tokens: int = 8000
    image_first: bool = False    # the model's own example puts the image before the text
    notes: str = ""
    variant_of: str = None       # a prompt variant of another reader, served by that reader's profile; chosen by the job's args

    @property
    def prompt_sha(self) -> str:
        return hashlib.sha256(self.prompt.encode("utf-8")).hexdigest()[:16]


def _p(model: str, *names: str) -> tuple:
    return tuple(os.path.join(MODELS, model, n) for n in names)


READERS: dict[str, Reader] = {
    "glm-ocr": Reader(
        "glm-ocr", "glm-ocr", "page-reader", "zhipu", "q8_0",
        (os.path.join(OLD_MODELS, "GLM-OCR-Q8_0.gguf"), os.path.join(OLD_MODELS, "mmproj-GLM-OCR-Q8_0.gguf")),
        PROMPT_GLM_OCR, "ggml-org's GLM-OCR guide, as the old estate's ec_pageread.vision_ocr ran it", "markdown",
        notes="the incumbent and the reference: the same weights, build and prompt the old estate's readings were made with"),
    "glm-ocr-textrec": Reader(
        "glm-ocr-textrec", "glm-ocr", "page-reader", "zhipu", "q8_0",
        (os.path.join(OLD_MODELS, "GLM-OCR-Q8_0.gguf"), os.path.join(OLD_MODELS, "mmproj-GLM-OCR-Q8_0.gguf")),
        PROMPT_GLM_OCR_CARD, "zai-org/GLM-OCR model card: the document-parsing prompt", "markdown", variant_of="glm-ocr",
        notes="the incumbent under its model card's own prompt (the queue item's default: run after pass two, keyed apart by prompt)"),
    "glm-ocr-f16": Reader(
        "glm-ocr-f16", "glm-ocr-f16", "trial-glm-ocr-f16", "zhipu", "f16",
        _p("glm-ocr", "GLM-OCR-f16.gguf", "mmproj-GLM-OCR-Q8_0.gguf"),
        PROMPT_GLM_OCR, "as glm-ocr", "markdown", notes="the incumbent's second compression level (3.1)"),
    "teleocr": Reader(
        "teleocr", "teleocr", "trial-teleocr", "qwen", "q8_0",
        _p("teleocr", "NaviDC-OCR-Q8_0.gguf", "NaviDC-OCR-mmproj-q8_0.gguf"),
        PROMPT_TELEOCR_TEXT, "bbsai/TeleOCR model card, the text task (tables come out in OTSL under the table task)", "markdown",
        system=SYSTEM_TELEOCR, image_first=True,
        notes="community conversion under the former name NaviDC-OCR; needs a patched model server (its PATCHES.md)"),
    "teleocr-f16": Reader(
        "teleocr-f16", "teleocr-f16", "trial-teleocr-f16", "qwen", "f16",
        _p("teleocr", "NaviDC-OCR-f16.gguf", "NaviDC-OCR-mmproj-f16.gguf"),
        PROMPT_TELEOCR_TEXT, "as teleocr", "markdown", system=SYSTEM_TELEOCR, image_first=True),
    "ovisocr2": Reader(
        "ovisocr2", "ovisocr2", "trial-ovisocr2", "qwen", "q8_0",
        _p("ovisocr2", "OvisOCR2-Q8_0.gguf", "mmproj-F16.gguf"),
        PROMPT_OVISOCR2, "Abiray/OvisOCR2-GGUF model card, the llama.cpp example", "markdown", thinking_off=True),
    "ovisocr2-f16": Reader(
        "ovisocr2-f16", "ovisocr2-f16", "trial-ovisocr2-f16", "qwen", "f16",
        _p("ovisocr2", "OvisOCR2-F16.gguf", "mmproj-F32.gguf"),
        PROMPT_OVISOCR2, "as ovisocr2", "markdown", thinking_off=True),
    "chandra-ocr-2": Reader(
        "chandra-ocr-2", "chandra-ocr-2", "trial-chandra", "qwen", "q8_0",
        _p("chandra-ocr-2", "chandra-ocr-2.Q8_0.gguf", "chandra-ocr-2.mmproj-f16.gguf"),
        PROMPT_CHANDRA, "datalab-to/chandra, chandra/prompts.py OCR_LAYOUT_PROMPT (the package's default prompt_type)", "html",
        thinking_off=True, max_tokens=12000,
        notes="weights under a modified OpenRAIL-M licence: on the before-selling legal list (ruling 49)"),
    "chandra-ocr-2-q4": Reader(
        "chandra-ocr-2-q4", "chandra-ocr-2-q4", "trial-chandra-q4", "qwen", "q4_k_m",
        _p("chandra-ocr-2", "chandra-ocr-2.Q4_K_M.gguf", "chandra-ocr-2.mmproj-Q8_0.gguf"),
        PROMPT_CHANDRA, "as chandra-ocr-2", "html", thinking_off=True, max_tokens=12000),
    "infinity-parser2-pro": Reader(
        "infinity-parser2-pro", "infinity-parser2-pro", "trial-infinity-q4", "qwen", "q4_k_m",
        _p("infinity-parser2-pro", "Infinity-Parser2-Pro-Q4_K_M.gguf", "Infinity-Parser2-Pro-mmproj-bf16.gguf"),
        PROMPT_INFINITY_DOC2MD, "infly-ai/INF-MLLM, infinity_parser2/prompts.py PROMPT_DOC2MD (the doc2md task)", "markdown",
        thinking_off=True, image_first=True,
        notes="the hub holds only a Q8_0 conversion (36.9 GB, larger than one card); the Q4_K_M is made here from it with the quantiser"),
    "infinity-parser2-pro-q8": Reader(
        "infinity-parser2-pro-q8", "infinity-parser2-pro-q8", "trial-infinity-q8", "qwen", "q8_0",
        _p("infinity-parser2-pro", "Infinity-Parser2-Pro-Q8_0.gguf", "Infinity-Parser2-Pro-mmproj-bf16.gguf"),
        PROMPT_INFINITY_DOC2MD, "as infinity-parser2-pro", "markdown", thinking_off=True, image_first=True,
        notes="served with the experts on the processor (--cpu-moe): the comparison level for the Q4_K_M, not a candidate"),
}

CHALLENGERS = ("teleocr", "ovisocr2", "chandra-ocr-2", "infinity-parser2-pro")
INCUMBENT = "glm-ocr"


def by_profile(profile: str, name: str = None) -> Reader | None:
    """The reader a profile serves; `name` picks a variant of it (the job's
    args), which must be served by the same profile."""
    if name:
        r = READERS.get(name)
        return r if r and r.profile == profile else None
    for r in READERS.values():
        if r.profile == profile and not r.variant_of:
            return r
    return None


def settings(reader: Reader, dpi: int, server_build: str = None) -> dict:
    """What a reading is stamped with: enough that two readings under
    different settings never collide (ruling 50), nothing that is a secret."""
    return {"dpi": int(dpi), "prompt": reader.prompt if len(reader.prompt) <= 40 else None, "prompt_sha": reader.prompt_sha,
            "system": reader.system, "level": reader.level, "temperature": 0.0, "max_tokens": reader.max_tokens,
            "thinking": "off" if reader.thinking_off else "default", "server_build": server_build,
            "weights": [os.path.basename(w) for w in reader.weights]}


def messages(reader: Reader, b64: str, media_type: str) -> list:
    image = {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{b64}"}}
    text = {"type": "text", "text": reader.prompt}
    content = [image, text] if reader.image_first else [text, image]
    out = []
    if reader.system:
        out.append({"role": "system", "content": reader.system})
    out.append({"role": "user", "content": content})
    return out


def extra(reader: Reader) -> dict:
    """The request fields beside the messages: temperature 0 for every
    reader; thinking off where the base model thinks."""
    out = {"temperature": 0.0, "max_tokens": reader.max_tokens}
    if reader.thinking_off:
        out["chat_template_kwargs"] = {"enable_thinking": False}
    return out
