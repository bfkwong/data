import sys
import re
import json
import urllib
import os
import base64
import requests
import mistletoe
from mistletoe.latex_renderer import LaTeXRenderer

OUTPUT_IMG_CNT = 0
OPERATING_PATH = ""

def openPynb(filename: str) -> dict:
    with open(filename, mode= "r", encoding= "utf-8") as f:
        pynbRaw = json.loads(f.read())["cells"]
    return pynbRaw

def parseImage(line: str) -> str:
    global OPERATING_PATH
    resMatch = re.match(r"!\[(?P<title>[\s\S]*?)\]\((?P<link>[\s\S]*?)\)", line).groupdict()
    if resMatch["link"][0:4] == "http":
        urllib.request.urlretrieve(resMatch["link"], "./LatexBook/image/" + resMatch["title"] + ".png")
    else:
        with open(OPERATING_PATH + resMatch["link"], "rb") as f:
            with open("./LatexBook/image/" + resMatch["link"] + ".png", "wb") as f2:
                f2.write(f.read())
    return "\\begin{figure}[h!]\\centering\\includegraphics[width=0.45\\paperwidth]{%s}\\end{figure}\n" \
            % ("image/" + resMatch["title"])

def parseCode(code: str) -> str:
    if re.match(r"# SETUP", code):
        return ""
    return "\\begin{lstlisting}[language=Python]\n%s\n\\end{lstlisting}\n" % (code)

def parseOutput(outputs: list) -> str:
    global OUTPUT_IMG_CNT
    latexOutput = []
    for output in outputs:
        if output["output_type"] == "execute_result":
            res = "\\small\\begin{verbatim}\n" + "".join(output["data"]["text/plain"]) + "\n\\end{verbatim}\n"
            latexOutput.append(res)
        elif output["output_type"] == "display_data":
            imageFileName = str(OUTPUT_IMG_CNT) + ".png"
            OUTPUT_IMG_CNT += 1
            if "data" in output and "image/png" in output["data"]:
                with open("./LatexBook/image/" + imageFileName, "wb") as fh:
                    fh.write(base64.decodebytes(bytes(output["data"]["image/png"].encode('utf-8'))))
                res = "\\begin{figure}[h!]\\centering\\includegraphics[width=0.45\\paperwidth]{%s}\\end{figure}\n" \
                % ("image/" + imageFileName)
                latexOutput.append(res)
            elif "data" in output and "text/plain" in output["data"]:
                res = "\\small\\begin{verbatim}\n" + "".join(output["data"]["text/plain"]) + "\n\\end{verbatim}\n"
                latexOutput.append(res)

    return "\n".join(latexOutput)

graphicsRE = r'(?P<pre>[\s\S]*)\\includegraphics{(?P<pngSrc>[\s\S]*?)}(?P<post>[\s\S]*)'
def parseIncludeGraphics(string):
    global OUTPUT_IMG_CNT
    res = re.search(graphicsRE, string)

    if res == None:
        return string

    res = res.groupdict()

    preRE = parseIncludeGraphics(res["pre"])
    postRE = parseIncludeGraphics(res["post"])

    if res["pngSrc"][0:4] == "http":
        urllib.request.urlretrieve(res["pngSrc"], "./LatexBook/image/" + str(OUTPUT_IMG_CNT) + ".png")
        body = "\\begin{figure}[h!]\\centering\\includegraphics[width=0.45\\paperwidth]{%s}\\end{figure}\n" % ("image/" + str(OUTPUT_IMG_CNT) + ".png")
        OUTPUT_IMG_CNT += 1
    else:
        with open(OPERATING_PATH + res["pngSrc"], "rb") as f:
            with open("./LatexBook/image/" + res["pngSrc"] + ".png", "wb") as f2:
                f2.write(f.read())
        body = "\\begin{figure}[h!]\\centering\\includegraphics[width=0.45\\paperwidth]{%s}\\end{figure}\n" % ("image/" + res["pngSrc"] + ".png")

    return preRE + body + postRE

sectionRE = r'(?P<pre>[\s\S]*)\\section{(?P<title>[\s\S]*?)}(?P<post>[\s\S]*)'
def parseSection(string):
    global OUTPUT_IMG_CNT
    res = re.search(sectionRE, string)

    if res == None:
        return string

    res = res.groupdict()

    preRE = parseSection(res["pre"])
    postRE = parseSection(res["post"])
    body = "\\chapter{%s}\\label{ch}" % (res["title"])

    return preRE + body + postRE

subsectionRE = r'(?P<pre>[\s\S]*)\\subsection{(?P<title>[\s\S]*?)}(?P<post>[\s\S]*)'
def parseSubSection(string):
    global OUTPUT_IMG_CNT
    res = re.search(subsectionRE, string)

    if res == None:
        return string

    res = res.groupdict()

    preRE = parseSubSection(res["pre"])
    postRE = parseSubSection(res["post"])
    body = "\\section{%s}\\label{ch}" % (res["title"])

    return preRE + body + postRE

subsubsectionRE = r'(?P<pre>[\s\S]*)\\subsubsection{(?P<title>[\s\S]*?)}(?P<post>[\s\S]*)'
def parseSubSubSection(string):
    global OUTPUT_IMG_CNT
    res = re.search(subsubsectionRE, string)

    if res == None:
        return string

    res = res.groupdict()

    preRE = parseSubSubSection(res["pre"])
    postRE = parseSubSubSection(res["post"])
    body = "\\subsection{%s}\\label{ch}" % (res["title"])

    return preRE + body + postRE

quotationRE = r'(?P<pre>[\s\S]*)\\begin{displayquote}\n(?P<title>[\s\S]*?)\\end{displayquote}(?P<post>[\s\S]*)'
def parseQuotation(string):
    res = re.search(quotationRE, string)

    if res == None:
        return string

    res = res.groupdict()

    preRE = parseQuotation(res["pre"])
    postRE = parseQuotation(res["post"])
    body = "\\begin{displayquote}" + res["title"] + "\\end{displayquote}"

    return preRE + body + postRE

mathJaxAlignRE = r'(?P<pre>[\s\S]*)\$\$ *\n* *\\begin{align}(?P<title>[\s\S]*?) *\n* *\\end{align}\$\$(?P<post>[\s\S]*)'
def parseMathJaxTags(string):
    res = re.search(mathJaxAlignRE, string)

    if res == None:
        return string

    res = res.groupdict()

    preRE = parseMathJaxTags(res["pre"])
    postRE = parseMathJaxTags(res["post"])
    body = "\\begin{align}" + res["title"] + "\\end{align}"

    return preRE + body + postRE

tagRE = r'(?P<pre>[\s\S]*)\\tag{[\s\S]*?}(?P<post>[\s\S]*)'
def parseRemoveTag(string):
    res = re.search(tagRE, string)

    if res == None:
        return string

    res = res.groupdict()

    preRE = parseRemoveTag(res["pre"])
    postRE = parseRemoveTag(res["post"])

    return preRE + postRE

hrefTags = r'(?P<pre>[\s\S]*)\\href{(?P<link>[\s\S]*?)}{(?P<text>[\s\S]*?)}(?P<post>[\s\S]*)'
def parseFootNoteTag(string):
    res = re.search(hrefTags, string)

    if res == None:
        return string

    res = res.groupdict()

    preRE = parseFootNoteTag(res["pre"])
    postRE = parseFootNoteTag(res["post"])
    body = res["text"] + "\\footnote{" + res["link"] + "}"

    return preRE + body + postRE


def postParser(string:str) -> str:
    parsed = parseIncludeGraphics(string)
    parsed = parseSection(parsed)
    parsed = parseSubSection(parsed)
    parsed = parseSubSubSection(parsed)
    parsed = parseQuotation(parsed)
    parsed = parseMathJaxTags(parsed)
    parsed = parseRemoveTag(parsed)
    parsed = parseFootNoteTag(parsed)
    return parsed

def pynbParser(indir: str, outfile: str):
    global OPERATING_PATH
    if not os.path.exists('./LatexBook/image'):
        os.makedirs('./LatexBook/image')

    OPERATING_PATH = indir + "/"
    fileInDir = [indir + "/" + x for x in os.listdir(indir) if re.match(r"[\s\S]*.ipynb$", x) and x != "pynbParser.ipynb"]
    fileInDir.sort()

    parsedCells = []
    for infile in fileInDir:
        print(infile)
        pynbRaw = openPynb(infile)

        for cell in pynbRaw:
            if cell["cell_type"] == "markdown":
                if cell["source"][0][:8] != "<a href=":
                    rendered = mistletoe.markdown("".join(cell["source"]), LaTeXRenderer)
                    latexRE = r'[\s\S]*\\begin{document}(?P<body>[\s\S]*)\\end{document}'
                    s = re.match(latexRE, rendered).groupdict()
                    s = postParser(s["body"])
                    parsedCells.append(s)
            elif cell["cell_type"] == "code":
                res = parseCode("".join(cell["source"]))
                parsedCells.append(res)
                res = parseOutput(cell["outputs"])
                parsedCells.append(res)
            else:
                print("Error: Encountered unknown cell type")
                exit(1)

        parsedCells.append("\n\n")

    if not os.path.exists("./LatexBook/" + indir):
        os.makedirs('./LatexBook/' + indir)

    with open("./LatexBook/" + indir + "/" + outfile, "w") as f:
        f.write("\n".join(parsedCells))

    OPERATING_PATH = ""
    return "\n".join(parsedCells)

def createLatexBook(configfilename):
    with open(configfilename, mode= "r", encoding= "utf-8") as f:
        config = json.loads(f.read())
    bookdir = config["book_directory"]

    if "main.tex" not in config["resources"]:
        print("Error: main.tex not provided in resources section of config file")
        return

    if not os.path.exists(bookdir):
        print("Error: Path does not exist")
        return

    if not os.path.exists('./LatexBook'):
        os.makedirs('./LatexBook')

    listDir = [x for x in os.listdir() if re.match(r"\d\d_.*", x)]
    listDir.sort()
    outputs = []

    main = requests.get(config["resources"]["main.tex"]).text
    main = main.split("@@@SPLIT@@@")

    main_written = [main[0]]

    print("===================================")
    print("STARTING PARSER")
    print("===================================")
    for folder in listDir:
        output = pynbParser(folder, "out.tex")
        outputs.append([folder, output])

        main_written.append("\include{" + folder + "/out" + "}")

    main_written.append(main[-1])
    main_written = "\n".join(main_written)

    print("===================================")
    print("WRITING RESOURCES")
    print("===================================")

    for key in config["resources"]:
        print(key)
        with open("./LatexBook/" + key, "w") as f:
            f.write(requests.get(config["resources"][key]).text)

    with open("./LatexBook/main.tex", "w") as f:
        f.write(main_written)

    print("===================================")
    print("FINISHED PARSING")
    print("===================================")

    return

def main():
    createLatexBook(sys.argv[1])
    return

if __name__ == '__main__':
    main()